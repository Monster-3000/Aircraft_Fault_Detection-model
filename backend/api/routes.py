import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.services.detector import DetectorService
from backend.services.explainer import ExplainerService
from backend.services.risk import calculate_risk
from backend.utils.image_utils import save_upload_file

router = APIRouter()

# Initialize services globally or via dependency injection
# Using global for simplicity in this version
MODEL_PATH = "backend/models/best.pt"
try:
    detector = DetectorService(MODEL_PATH)
    explainer = ExplainerService(detector.model)
except Exception as e:
    print(f"Error loading models: {e}")
    detector = None
    explainer = None

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
            
        # 3. Generate XAI Explanation
        explainer.generate_heatmap(upload_path, xai_path)
        
        # Convert absolute paths to relative URLs or frontend-accessible paths
        # In a real app this would be a static URL, here we'll just pass a relative path
        # Assuming frontend runs and can access /outputs via a static mount
        
        explanation_text = "No defects were detected on the aircraft surface."
        report_path = None
        if enriched_defects:
            defect = enriched_defects[0]  # generate report for the first/main defect
            
            # Determine specific AI explanation
            if defect["class_name"] == "crack":
                specific_exp = "The AI focused on elongated high-contrast regions with strong edge discontinuity, matching crack patterns learned during training."
            elif defect["class_name"] == "dent":
                specific_exp = "The AI focused on localized curved surface deformation with shadow variations similar to dent samples."
            else:
                specific_exp = "The AI detected a structural anomaly based on learned visual features."
                
            explanation_text = f"The model detected {len(enriched_defects)} defect(s): {', '.join([d['class_name'] for d in enriched_defects])}. {specific_exp}"
            
            # Generate the Text Report File
            report_path_abs = os.path.abspath(f"outputs/explanations/{req_id}_report.txt")
            with open(report_path_abs, "w") as f:
                f.write("========== DRISHTI XAI REPORT ==========\n\n")
                f.write(f"Image : {req_id}_original.jpg\n")
                f.write(f"Aircraft Section : {defect['location']}\n")
                f.write(f"Detected Damage : {defect['class_name']}\n")
                f.write(f"Confidence : {defect['confidence']}\n")
                # bbox is [x1, y1, x2, y2]
                x1, y1, x2, y2 = defect["bbox"]
                f.write(f"Center X : {(x1+x2)/2}\n")
                f.write(f"Center Y : {(y1+y2)/2}\n")
                f.write(f"Bounding Box Width : {x2-x1}\n")
                f.write(f"Bounding Box Height : {y2-y1}\n")
                f.write(f"Severity : {defect['severity']}\n")
                f.write(f"Urgency : {defect['urgency']}\n")
                f.write(f"Priority : {defect['priority']}\n\n")
                
                f.write("AI Explanation\n")
                f.write("-----------------------------\n")
                f.write(specific_exp + "\n\n")
                
                f.write("Recommendation\n")
                f.write("-----------------------------\n")
                f.write(str(defect["recommendation"]))
                
            report_path = f"/static/explanations/{req_id}_report.txt"

        return {
            "detections": enriched_defects,
            "explanation": explanation_text,
            "explanation_path": f"/static/explanations/{req_id}_xai.jpg",
            "report_path": report_path,
            "original_image_path": f"/static/detections/{req_id}_original.jpg"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")
