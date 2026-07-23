import time
import uuid
import json
import asyncio
import google.generativeai as genai
from typing import Dict, Any
from backend.app.core.config import settings
from backend.app.services.mongo_service import MongoService

async def asyncio_sleep_wrapper(seconds: float):
    await asyncio.sleep(seconds)

# Initialize Mongo DB service helper
mongo_service = MongoService()

class CriticService:
    def __init__(self):
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)

    async def run_async_critic(self, client_id: str, tiptap_json: Dict[str, Any]):
        """Asynchronously processes report edits and extracts preferences into MongoDB notifications."""
        # Standard sleep to simulate computational processing delay
        await asyncio_sleep_wrapper(1)

        extracted_fact = None
        message = None

        if settings.gemini_api_key:
            try:
                prompt = (
                    "You are a behavioral Critic loop. Analyze the following Tiptap report layout document JSON. "
                    "Extract any repetitive formatting rules, template definitions, or styles that the user might want "
                    "saved for future generations. "
                    "Respond ONLY with a valid JSON payload containing:\n"
                    "{\n"
                    "  'extracted_fact': 'A single declarative rule statement (e.g. Always format Q3 numbers in a table)',\n"
                    "  'message': 'A message for the user asking to approve this rule'\n"
                    "}\n"
                    "If no clear preference can be extracted, return empty fields.\n\n"
                    f"Document JSON:\n{json.dumps(tiptap_json)}"
                )
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    generation_config={"response_mime_type": "application/json"}
                )
                response = model.generate_content(contents=prompt)
                res_data = json.loads(response.text)
                extracted_fact = res_data.get("extracted_fact")
                message = res_data.get("message")
            except Exception:
                pass

        # Fallback simulation if no API key or generation failed
        if not extracted_fact:
            extracted_fact = f"Always use the clean financial layout template for {client_id} corporate reporting."
            message = f"I noticed you corrected the {client_id} report structure. Remember this rule?"

        # Save to database in pending_approval state
        notification = {
            "_id": f"notif_{uuid.uuid4().hex[:8]}",
            "client_id": client_id,
            "status": "pending_approval",
            "message": message,
            "extracted_fact": extracted_fact,
            "meta_tags": {"domain": "formatting_preference"},
            "created_at": int(time.time())
        }
        mongo_service.insert_notification(notification)
