def calculate_risk(defect: str) -> dict:
    """
    Returns risk information based on the type of defect detected.
    Classes:
      0 = Dent
      1 = Fastener Damage
      2 = Rupture
    """
    d = defect.lower() if isinstance(defect, str) else ""
    if "rupture" in d:
        return {
            "severity": 95,
            "urgency": "High",
            "priority": "#1",
            "recommendation": "Immediate Structural Repair / Ground Aircraft (AOG)"
        }
    elif "fastener" in d:
        return {
            "severity": 85,
            "urgency": "High",
            "priority": "#1",
            "recommendation": "Inspect Fastener Integrity & Torque / Replace Fastener"
        }
    elif "dent" in d:
        return {
            "severity": 70,
            "urgency": "Medium",
            "priority": "#2",
            "recommendation": "Schedule Surface Repair & Depth Inspection"
        }
    
    return {
        "severity": 50,
        "urgency": "Low",
        "priority": "None",
        "recommendation": "Monitor during routine maintenance"
    }

