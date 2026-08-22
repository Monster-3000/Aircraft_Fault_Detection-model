from pydantic import BaseModel
from typing import List

class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

class Defect(BaseModel):
    class_name: str
    confidence: float
    bbox: List[float]
    location: str
    severity: int
    urgency: str
    priority: str
    recommendation: str

class DetectionResponse(BaseModel):
    detections: List[Defect]
    explanation: str
    explanation_path: str
    original_image_path: str
