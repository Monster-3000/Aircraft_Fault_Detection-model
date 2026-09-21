import os
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# Configure the API key
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def analyze_aircraft_damage(image_path: str) -> str:
    """
    Uses Gemini Vision to analyze the aircraft image and find obvious damage.
    """
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        return "VLM Disabled: Please add your GEMINI_API_KEY to the .env file."
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = Image.open(image_path)
        
        prompt = (
            "You are an expert aviation structural inspector. Look at this image of an aircraft. "
            "Ignore minor background noise (like wheels on carts or distant objects). "
            "Focus strictly on the primary aircraft structure. "
            "Is there any massive, obvious structural damage (like a completely crushed nose, massive dents, "
            "or severe structural failure)? If so, accurately describe exactly what and where the damage is "
            "using proper aircraft anatomy (e.g., radome, main fuselage, wings, empennage). "
            "If the aircraft looks perfectly intact, just say 'No severe structural damage visually detected.' "
            "Keep the response professional, highly accurate, and strictly under 3 sentences."
        )
        
        response = model.generate_content([prompt, img])
        return response.text.strip()
    except Exception as e:
        return f"VLM Analysis Failed: {str(e)}"

