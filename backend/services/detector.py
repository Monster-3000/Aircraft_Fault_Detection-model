import os
from ultralytics import YOLO

class DetectorService:
    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}")
        self.model = YOLO(model_path)
        
        # Load the parts detection model
        parts_model_path = os.path.join(os.path.dirname(model_path), 'parts_model.pt')
        if os.path.exists(parts_model_path):
            self.parts_model = YOLO(parts_model_path)
        else:
            self.parts_model = None
    
    def _is_inside(self, inner_box, outer_box):
        cx = (inner_box[0] + inner_box[2]) / 2
        cy = (inner_box[1] + inner_box[3]) / 2
        return (outer_box[0] <= cx <= outer_box[2]) and (outer_box[1] <= cy <= outer_box[3])

    def predict(self, image_path: str):
        """
        Runs inference on the provided image and returns structured predictions.
        """
        results = self.model(image_path, conf=0.1)
        
        parts = []
        parts_results = None
        if self.parts_model:
            parts_results = self.parts_model(image_path, conf=0.1)
            for pr in parts_results:
                for box in pr.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    parts.append({
                        "name": self.parts_model.names[cls_id],
                        "bbox": [x1, y1, x2, y2],
                        "conf": conf
                    })
                    
        defects = []
        import cv2
        
        for result in results:
            res_plotted = result.plot()
            if parts_results:
                for pr in parts_results:
                    # Draw parts on top
                    res_plotted = pr.plot(img=res_plotted)
            cv2.imwrite(image_path, res_plotted)
            
            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                
                # Get coordinates
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                bbox = [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)]
                
                location = "Unknown"
                if parts:
                    best_part = None
                    best_score = -1
                    for p in parts:
                        if self._is_inside(bbox, p["bbox"]):
                            if p["conf"] > best_score:
                                best_score = p["conf"]
                                best_part = p["name"]
                    if best_part:
                        location = best_part
                
                defects.append({
                    "class": self.model.names[cls_id],
                    "confidence": round(conf, 2),
                    "bbox": bbox,
                    "location": location
                })
        
        return defects
