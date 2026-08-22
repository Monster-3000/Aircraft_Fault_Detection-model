import pytest
from backend.services.detector import DetectorService
import os

def test_detector_initialization():
    # Should raise error for invalid path
    with pytest.raises(FileNotFoundError):
        DetectorService("invalid/path.pt")

def test_detector_inference():
    # Only test if model exists
    model_path = "backend/models/best.pt"
    if os.path.exists(model_path) and os.path.exists("images/test_aircraft.jpg"):
        detector = DetectorService(model_path)
        results = detector.predict("images/test_aircraft.jpg")
        
        assert isinstance(results, list)
        if len(results) > 0:
            assert "class" in results[0]
            assert "confidence" in results[0]
            assert "bbox" in results[0]
