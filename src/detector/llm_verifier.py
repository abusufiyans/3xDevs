import os
import json
import re
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.environ.get("GROQ_API_KEY")

if api_key:
    client = Groq(api_key=api_key)
else:
    client = None
    print("Warning: GROQ_API_KEY not set.")


def check_authenticity_with_llm(text: str, language: str) -> dict:
    if not client:
        return {
            "verdict": "uncertain",
            "confidence": 50,
            "explanation": "LLM verification is currently unavailable.",
            "flagged": []
        }

    try:
        prompt = f"""You are a fact-checking assistant with access to your training knowledge.

Analyze the following text and determine if it is factually accurate, misleading, or uncertain.

Important rules:
- If the claim matches known facts from your training data, mark it as "real"
- If the claim contradicts known facts, mark it as "fake"  
- If you cannot verify the claim with confidence, mark it as "uncertain"
- Do NOT flag text just because it sounds sensational or dramatic
- NEWS from credible sources about real events should generally be "real" or "uncertain", not "fake"
- Only mark as "fake" if you are confident the claim is factually wrong

Return ONLY valid JSON in this exact format:
{{
    "verdict": "fake" or "real" or "uncertain",
    "confidence": <integer 0-100>,
    "explanation": "<explain what you know about this claim and why you gave this verdict>",
    "flagged": ["<specific part of the claim that is questionable, if any>"]
}}

Text to analyze:
"{text}"
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a misinformation detection expert. You analyze text and return ONLY valid JSON. No markdown, no explanation outside the JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
        )

        result_text = response.choices[0].message.content.strip()

        # Strip markdown code blocks if present
        json_match = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL)
        if json_match:
            result_text = json_match.group(1)

        parsed = json.loads(result_text)

        verdict = str(parsed.get("verdict", "uncertain"))
        if verdict not in ["fake", "real", "uncertain"]:
            verdict = "uncertain"

        confidence = int(parsed.get("confidence", 50))
        explanation = str(parsed.get("explanation", "No explanation provided."))
        flagged = parsed.get("flagged", [])
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
            "explanation": "An error occurred while analyzing the text.",
            "flagged": []
        }