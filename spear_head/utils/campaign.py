from google import genai
from dotenv import load_dotenv
import os
import json

load_dotenv()


def generate_campaign_details(campaign: 'Campaign') -> tuple[str, str, str]:
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key is None:
            print("Error: GEMINI_API_KEY not set in environment variables.")
            return ("Unnamed Campaign", "No description available.", "LOW")
        
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=[
            {
                "role": "model",
                "parts": [{
                    "text": """You are an automated security campaign analysis engine.

You will receive data describing a single security campaign.
The campaign contains multiple low-level events (network, process, file, or alert events).
Your task is to generate a concise, human-readable campaign summary.

Rules you MUST follow:
- You MUST return ONLY valid JSON.
- Do NOT include markdown, comments, explanations, or extra text.
- Do NOT wrap the JSON in code blocks.
- The JSON MUST contain exactly these keys:
  - "name": a short descriptive campaign name (string, max 10 words)
  - "description": a concise technical summary of the campaign (string, 1-3 sentences)
  - "severity": one of "LOW", "MEDIUM", or "HIGH", based on the overall risk level of the campaign.
- If the campaign intent is unclear, choose a neutral, non-alarmist name and description.
- Do NOT invent events or facts not present in the input.
- Do NOT include confidence scores or metadata.

Output format (exact structure required):
{
  "name": "<string>",
  "description": "<string>",
  "severity": "<LOW|MEDIUM|HIGH>"
}
"""
                }]
            },
            {
                "role": "user",
                "parts": [{
                    "text": repr(campaign)
                }]
            }
        ]
        )

        try:
            content = response.text
            if not content:
                print("Error: Empty response from Gemini API.")
                return ("Unnamed Campaign", "No description available.", "LOW")
            data = json.loads(content)
            name = data.get("name", "Unnamed Campaign")
            description = data.get("description", "No description available.")
            severity = data.get("severity", "LOW")
            if severity not in {"LOW", "MEDIUM", "HIGH"}:
                severity = "LOW"
            return (name, description, severity)
        except (json.JSONDecodeError, KeyError) as e:
            print("Error parsing response from Gemini API:", e)
            return ("Unnamed Campaign", "No description available.", "LOW")
    except Exception as e:
        print("Error generating campaign details:", e)
        return ("Unnamed Campaign", "No description available.", "LOW")