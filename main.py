from detector import detect_defects
from risk_engine import calculate_risk

images = ["images/test_aircraft.jpg", "images/internet_test.jpg"]

for image in images:
    print(f"\n--- TESTING IMAGE: {image} ---")
    defects = detect_defects(image)

    for defect in defects:
        risk = calculate_risk(defect["class"])
        print("\nDETECTION")
        print("Class:", defect["class"])
        print("Confidence:", defect["confidence"])
        print("Location:", defect.get("location", "Unknown"))
        print("\nRISK")
        print("Severity:", risk["severity"])
        print("Urgency:", risk["urgency"])
        print("Priority:", risk["priority"])
        print("Recommendation:", risk["recommendation"])