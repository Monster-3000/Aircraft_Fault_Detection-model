import os
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_predict_endpoint_no_file():
    response = client.post("/api/predict")
    assert response.status_code == 422 # Validation error for missing file

def test_predict_endpoint_invalid_file():
    response = client.post(
        "/api/predict",
        files={"file": ("test.txt", b"hello", "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "File provided is not an image."

def test_predict_endpoint_valid_file():
    # Only run if model exists
    if not os.path.exists("backend/models/best.pt"):
        pytest.skip("Model not found")
        
    image_path = "images/test_aircraft.jpg"
    if not os.path.exists(image_path):
        pytest.skip("Test image not found")
        
    with open(image_path, "rb") as f:
        response = client.post(
            "/api/predict",
            files={"file": ("test_aircraft.jpg", f, "image/jpeg")}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert "explanation_path" in data
    assert "original_image_path" in data
