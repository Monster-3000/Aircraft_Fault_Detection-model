import os
import uuid
import json
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from backend.services.detector import DetectorService
from backend.services.explainer import ExplainerService
from backend.services.risk import calculate_risk
from backend.utils.image_utils import save_upload_file

router = APIRouter()

# Initialize services globally or via dependency injection
# Model path is configurable via AIRCRAFT_MODEL_PATH environment variable
MODEL_PATH = os.getenv("AIRCRAFT_MODEL_PATH", "models/best.pt" if os.path.exists("models/best.pt") else "backend/models/best.pt")
try:
    detector = DetectorService(MODEL_PATH)
    explainer = ExplainerService(detector.model)
except Exception as e:
    print(f"Error loading models: {e}")
    detector = None
    explainer = None

class ExplainRequest(BaseModel):
    req_id: str


@router.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not detector or not explainer:
        raise HTTPException(status_code=500, detail="Models failed to load.")
        
    if file.content_type is None or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")

    # Generate unique ID for this request
    req_id = str(uuid.uuid4())
    
    # Define paths
    upload_path = os.path.abspath(f"outputs/detections/{req_id}_original.jpg")
    xai_path = os.path.abspath(f"outputs/explanations/{req_id}_xai.jpg")
    
    # Ensure directories exist
    os.makedirs("outputs/detections", exist_ok=True)
    os.makedirs("outputs/explanations", exist_ok=True)
    
    # Save uploaded file
    try:
        save_upload_file(file, upload_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save image: {e}")
        
    try:
        # 1. Run detection
        raw_defects = detector.predict(upload_path)
        
        # 2. Enrich with risk information
        enriched_defects = []
        for d in raw_defects:
            risk = calculate_risk(d["class"])
            enriched_defects.append({
                "class_name": d["class"],
                "confidence": d["confidence"],
                "bbox": d["bbox"],
                "location": d.get("location", "Unknown"),
                "severity": risk["severity"],
                "urgency": risk["urgency"],
                "priority": risk["priority"],
                "recommendation": risk["recommendation"]
            })
            
        # Save detection data to JSON so /explain can pick it up
        data_path = os.path.abspath(f"outputs/detections/{req_id}_data.json")
        with open(data_path, "w") as f:
            json.dump(enriched_defects, f)

        return {
            "req_id": req_id,
            "detections": enriched_defects,
            "original_image_path": f"/static/detections/{req_id}_original.jpg"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

@router.post("/explain")
async def explain(request: ExplainRequest):
    if not explainer:
        raise HTTPException(status_code=500, detail="Models failed to load.")
        
    req_id = request.req_id
    upload_path = os.path.abspath(f"outputs/detections/{req_id}_original.jpg")
    data_path = os.path.abspath(f"outputs/detections/{req_id}_data.json")
    xai_path = os.path.abspath(f"outputs/explanations/{req_id}_xai.jpg")
    
    if not os.path.exists(upload_path) or not os.path.exists(data_path):
        raise HTTPException(status_code=404, detail="Detection data not found for this request ID.")
        
    try:
        with open(data_path, "r") as f:
            enriched_defects = json.load(f)
            
        # 3. Generate XAI Explanation
        explainer.generate_heatmap(upload_path, xai_path)
        
        explanation_text = "No defects were detected on the aircraft surface."
        report_path = None
        if enriched_defects:
            defect = enriched_defects[0]  # generate report for the first/main defect
            
            # Determine specific AI explanation based on new YOLO11s defect classes
            cls_lower = defect["class_name"].lower()
            if "rupture" in cls_lower:
                specific_exp = "The AI focused on severe material tearing, fracture boundaries, and structural continuity breaks matching rupture patterns learned during training."
            elif "fastener" in cls_lower:
                specific_exp = "The AI focused on localized hardware anomalies, missing rivets/screws, or stress deformation surrounding fastener heads."
            elif "dent" in cls_lower:
                specific_exp = "The AI focused on localized curved surface deformation with shadow variations similar to dent samples."
            else:
                specific_exp = f"The AI detected a structural anomaly ({defect['class_name']}) based on learned visual features."
                
            # Estimate Aircraft Section from Bounding Box
            import cv2
            img = cv2.imread(upload_path)
            h, w = img.shape[:2] if img is not None else (1000, 1000)

            x1, y1, x2, y2 = defect["bbox"]
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            
            guessed_section = "Main Fuselage"
            if cx < w * 0.25 or cx > w * 0.75:
                guessed_section = "Wings / Outer Engine / Winglets"
            elif cx > w * 0.8:
                guessed_section = "Empennage (Tail Section)"
            elif cx < w * 0.15:
                guessed_section = "Nose / Radome / Cockpit"
            elif cy < h * 0.3:
                guessed_section = "Upper Fuselage / Crown"
            elif cy > h * 0.7:
                guessed_section = "Lower Fuselage / Belly / Landing Gear"
                
            defect['location'] = guessed_section
            
            # Enhancing the text explanation
            anatomy_exp = (
                f"\nSpatial Analysis: The bounding box was localized in the {guessed_section}. "
                "In aircraft anatomy: "
                "\n - The Radome/Nose houses sensitive radar equipment."
                "\n - The Cockpit is the flight deck."
                "\n - The Fuselage is the main passenger/cargo body."
                "\n - The Wings provide lift and house fuel (often with Winglets to reduce drag)."
                "\n - The Empennage is the tail section (Vertical/Horizontal Stabilizers) controlling pitch and yaw."
                "\n - The Engines provide thrust (e.g., Trijet setups have side and center engines)."
            )
                
            explanation_text = f"YOLO detected {len(enriched_defects)} defect(s): {', '.join([d['class_name'] for d in enriched_defects])}. {specific_exp} It localized this to the {guessed_section}."
            
            # Generate the Text Report File
            report_path_abs = os.path.abspath(f"outputs/explanations/{req_id}_report.txt")
            with open(report_path_abs, "w") as f:
                f.write("========== DRISHTI XAI REPORT ==========\n\n")
                f.write(f"Image : {req_id}_original.jpg\n")
                f.write(f"Aircraft Section : {defect['location']}\n")
                f.write(f"Detected Damage : {defect['class_name']}\n")
                f.write(f"Confidence : {defect['confidence']}\n")
                f.write(f"Center X : {cx}\n")
                f.write(f"Center Y : {cy}\n")
                f.write(f"Bounding Box Width : {x2-x1}\n")
                f.write(f"Bounding Box Height : {y2-y1}\n")
                f.write(f"Severity : {defect['severity']}\n")
                f.write(f"Urgency : {defect['urgency']}\n")
                f.write(f"Priority : {defect['priority']}\n\n")
                
                f.write("YOLO Explanation & Anatomy\n")
                f.write("-----------------------------\n")
                f.write(specific_exp + "\n")
                f.write(anatomy_exp + "\n\n")
                
                f.write("Recommendation\n")
                f.write("-----------------------------\n")
                f.write(str(defect["recommendation"]))
                
            report_path = f"/static/explanations/{req_id}_report.txt"

        return {
            "explanation": explanation_text,
            "explanation_path": f"/static/explanations/{req_id}_xai.jpg",
            "report_path": report_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation generation failed: {e}")

