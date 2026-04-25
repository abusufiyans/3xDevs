import os
import google.generativeai as genai

# Try to get the API key from environment variables
api_key = os.environ.get("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    # Using gemini-1.5-flash as it's the recommended model for text tasks
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None
    print("Warning: GEMINI_API_KEY environment variable not set. LLM analysis will be disabled.")

def check_authenticity_with_llm(text: str, language: str) -> dict:
    """
    Checks the authenticity of the given text using Gemini.
    """
    if not model:
         return {
             "verdict": "uncertain",
             "confidence": 50,
             "explanation": "LLM verification is currently unavailable because the API key is not configured.",
             "flagged": []
         }

    try:
        prompt = f"""
        Analyze the following text (which is in {language}) to determine if it is true, fake/misleading news, or uncertain.
        
        Text to analyze:
        "{text}"
        
        Provide your response in the following JSON format:
        {{
            "verdict": "fake" | "real" | "uncertain",
            "confidence": <integer between 0 and 100>,
            "explanation": "<A clear explanation of why it is fake/real/uncertain, written in {language}. Keep it concise and mention any known facts.>",
            "flagged": ["<list of questionable phrases or claims from the text, if any>"]
        }}
        
        Ensure the response is ONLY valid JSON.
        """
        
        response = model.generate_content(prompt)
        
        # Parse the JSON response
        import json
        import re
        
        # Extract json content if it's wrapped in markdown blocks
        result_text = response.text
        json_match = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL)
        if json_match:
            result_text = json_match.group(1)
            
        parsed_result = json.loads(result_text)
        
        # Ensure we have all expected fields with valid types
        verdict = str(parsed_result.get("verdict", "uncertain"))
        if verdict not in ["fake", "real", "uncertain"]:
            verdict = "uncertain"
            
        confidence = parsed_result.get("confidence", 50)
        try:
             confidence = int(confidence)
        except ValueError:
             confidence = 50
             
        explanation = str(parsed_result.get("explanation", "Could not generate a clear explanation."))
        
        flagged = parsed_result.get("flagged", [])
        if not isinstance(flagged, list):
             flagged = []
             
        return {
            "verdict": verdict,
            "confidence": confidence,
            "explanation": explanation,
            "flagged": flagged
        }

    except Exception as e:
         print(f"LLM API Error: {e}")
         return {
             "verdict": "uncertain",
             "confidence": 50,
             "explanation": "An error occurred while verifying the information with the AI model.",
             "flagged": []
         }
