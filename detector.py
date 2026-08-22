import os
from ultralytics import YOLO

model = YOLO("models/best.pt" if os.path.exists("models/best.pt") else "backend/models/best.pt")

parts_model_path = "models/parts_model.pt" if os.path.exists("models/parts_model.pt") else "backend/models/parts_model.pt"
parts_model = YOLO(parts_model_path) if os.path.exists(parts_model_path) else None

def get_center(box):
    return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)

def is_inside(inner_box, outer_box):
    cx, cy = get_center(inner_box)
    return (outer_box[0] <= cx <= outer_box[2]) and (outer_box[1] <= cy <= outer_box[3])

def detect_defects(image_path):
    results = model(image_path)
    
    parts = []
    if parts_model:
        parts_results = parts_model(image_path)
        for pr in parts_results:
            for box in pr.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                parts.append({
                    "name": parts_model.names[cls],
                    "bbox": [x1, y1, x2, y2],
                    "conf": conf
                })

    defects = []

    for result in results:
        for box in result.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            bbox = [x1, y1, x2, y2]
            
            location = "Unknown"
            if parts:
                best_part = None
                best_score = -1
                for p in parts:
                    if is_inside(bbox, p["bbox"]) and p["conf"] > best_score:
                        best_score = p["conf"]
                        best_part = p["name"]
                if best_part:
                    location = best_part

            defects.append({
                "class": model.names[cls],
                "confidence": round(conf, 2),
                "location": location
            })

    return defects