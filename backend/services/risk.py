def calculate_risk(defect: str) -> dict:
    """
    Returns risk information based on the type of defect detected.
    """
    if defect == "crack":
        return {
            "severity": 95,
            "urgency": "High",
            "priority": "#1",
            "recommendation": "Immediate Inspection"
        }
    elif defect == "dent":
        return {
            "severity": 70,
            "urgency": "Medium",
            "priority": "#2",
            "recommendation": "Schedule Repair"
        }
    elif defect == "corrosion":
        return {
            "severity": 80,
            "urgency": "High",
            "priority": "#1",
            "recommendation": "Inspect Surface Integrity"
        }
    
    return {
        "severity": 0,
        "urgency": "Low",
        "priority": "None",
        "recommendation": "No action required"
    }
