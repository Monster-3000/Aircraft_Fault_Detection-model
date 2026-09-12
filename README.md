# DRISHTI - Aircraft Surface Damage Inspection System

An Explainable AI-based web application for detecting and analyzing aircraft surface damage using a YOLOv8 model and Eigen-CAM for AI explanations.

## Prerequisites
Make sure you have Python installed, then install the dependencies:
```powershell
pip install -r requirements.txt
```

## How to Run

To run the application, open a terminal in the root of the project directory (`d:\Software_Project`) and execute the following commands:

```powershell
# Set the PYTHONPATH to include the root directory
$env:PYTHONPATH = "d:\Software_Project"

# Start the FastAPI server using Uvicorn
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## How to Use
Once the server is running:
1. Open your web browser.
2. Navigate to [http://localhost:8000](http://localhost:8000).
3. Upload an aircraft inspection image (such as the ones in the `images/` directory).
4. The system will process the image and display the original image with bounding boxes, an Explainable AI (XAI) heatmap, and the structural risk analysis.
