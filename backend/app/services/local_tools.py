import json
from typing import Dict, Any, List
import google.generativeai as genai
from backend.app.core.config import settings
from backend.app.core.exceptions import ValidationError
from backend.app.mcp_mocks.ga4_mock import get_ga4_metrics
from backend.app.mcp_mocks.quickbooks_mock import get_quickbooks_data
from backend.app.services.sqlite_service import SQLiteService

# Initialize SQLite database service
db_service = SQLiteService()

class LocalToolsManager:
    def __init__(self):
        # Configure Gemini API connection
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)

    def execute_tool(self, name: str, params: Dict[str, Any], client_id: str) -> Any:
        """Executes a matching local python function or database query constraint."""
        if name == "get_ga4_metrics":
            return get_ga4_metrics(client_id)
        elif name == "get_quickbooks_data":
            return get_quickbooks_data(client_id)
        elif name == "query_client_vault":
            query_name = params.get("query_name")
            query_params = params.get("params", {})
            if not query_name:
                raise ValidationError("Missing 'query_name' in database tool call.")
            return db_service.run_query(query_name, query_params, client_id)
        else:
            raise ValidationError(f"Unknown local tool execution path: {name}")

    async def execute_in_app_loop(self, user_prompt: str, context: List[str], blueprint: Dict[str, Any]) -> dict:
        """Runs the Gemini structured compilation loop incorporating tool and blueprint contexts."""
        if not settings.gemini_api_key:
            # Sandbox fallback payload if GEMINI_API_KEY is not defined
            return self._get_fallback_tiptap(user_prompt)

        genai.configure(api_key=settings.gemini_api_key)
        client_id = blueprint.get("client_id", "client_abc")
        
        # Step 1: Pre-fetch metrics data locally to feed variables straight to LLM context pool
        ga4_data = get_ga4_metrics(client_id)
        qb_data = get_quickbooks_data(client_id)
        projects = db_service.run_query("get_projects", {}, client_id)

        # Assemble prompt system instructions
        system_instruction = (
            "You are an expert report compiler. You will generate a clean Tiptap document JSON structure.\n"
            f"Target Client ID: {client_id}\n"
            f"Formatting Preference Rules:\n" + "\n".join([f"- {c}" for c in context]) + "\n"
            f"Original Layout Blueprint:\n{json.dumps(blueprint.get('tiptap_schema_blueprint', {}))}\n\n"
            "Live Extracted Data context:\n"
            f"- GA4: {json.dumps(ga4_data)}\n"
            f"- QuickBooks: {json.dumps(qb_data)}\n"
            f"- SQLite Projects: {json.dumps(projects)}\n\n"
            "Respond ONLY with a valid, clean JSON payload matching the Tiptap structure: "
            "{\"type\": \"doc\", \"content\": [...]}. No markdown wrap, no explanations."
        )

        candidate_models = ["gemini-1.5-flash", "gemini-2.5-flash"]
        last_exception = None

        for m_name in candidate_models:
            clean_model_name = m_name.replace("models/", "")
            for gen_config in [{"response_mime_type": "application/json"}, None]:
                try:
                    if gen_config:
                        model = genai.GenerativeModel(
                            model_name=clean_model_name,
                            generation_config=gen_config
                        )
                    else:
                        model = genai.GenerativeModel(model_name=clean_model_name)

                    response = model.generate_content(
                        contents=[system_instruction, f"User Request: {user_prompt}"]
                    )

                    if response and response.text:
                        raw_text = response.text.strip()
                        if raw_text.startswith("```"):
                            lines = raw_text.splitlines()
                            if lines[0].startswith("```"):
                                lines = lines[1:]
                            if lines and lines[-1].startswith("```"):
                                lines = lines[:-1]
                            raw_text = "\n".join(lines).strip()

                        tiptap_json = json.loads(raw_text)
                        if isinstance(tiptap_json, dict) and tiptap_json.get("type") == "doc":
                            return tiptap_json
                except Exception as e:
                    last_exception = e
                    continue

        # Graceful error validation boundary
        return {
            "type": "doc",
            "content": [
                {"type": "heading", "attrs": {"level": 1}, "content": [{"type": "text", "text": "Generation Failure"}]},
                {"type": "paragraph", "content": [{"type": "text", "text": f"Error message details: {str(last_exception or 'Model service error')}"}]}
            ]
        }

    def _get_fallback_tiptap(self, user_prompt: str) -> dict:
        """Fallback JSON structure for sandbox environments without API keys."""
        return {
            "type": "doc",
            "content": [
                {"type": "heading", "attrs": {"level": 1}, "content": [{"type": "text", "text": "Sandbox Simulation Report"}]},
                {"type": "paragraph", "content": [
                    {"type": "text", "text": f"Simulated generation for request: '{user_prompt}'. "},
                    {"type": "text", "text": "Note: Configure GEMINI_API_KEY to execute live model calls.", "marks": [{"type": "bold"}]}
                ]}
            ]
        }
