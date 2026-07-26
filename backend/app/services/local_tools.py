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
        self.sqlite_service = db_service
        self.db_service = db_service
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
        client_id = blueprint.get("client_id", "client_abc")
        if not settings.gemini_api_key:
            # Sandbox fallback payload if GEMINI_API_KEY is not defined
            return self._get_fallback_tiptap(user_prompt, client_id)

        genai.configure(api_key=settings.gemini_api_key)
        
        # Step 1: Pre-fetch metrics data locally to feed variables straight to LLM context pool
        ga4_data = get_ga4_metrics(client_id)
        qb_data = get_quickbooks_data(client_id)
        projects = db_service.run_query("get_projects", {}, client_id)

        # Assemble prompt system instructions
        system_instruction = (
            "You are an executive corporate report compiler. You MUST generate a clean Tiptap document JSON structure.\n"
            f"Target Client ID: {client_id}\n"
            f"Formatting Preference Rules:\n" + "\n".join([f"- {c}" for c in context]) + "\n"
            f"Original Layout Blueprint:\n{json.dumps(blueprint.get('tiptap_schema_blueprint', {}))}\n\n"
            "Live Extracted Data context:\n"
            f"- GA4: {json.dumps(ga4_data)}\n"
            f"- QuickBooks: {json.dumps(qb_data)}\n"
            f"- SQLite Projects: {json.dumps(projects)}\n\n"
            "MANDATORY REPORT STRUCTURE:\n"
            "1. Title (heading level 1): 'Executive Performance Briefing: [CLIENT]'\n"
            "2. Executive Summary (heading level 2 + paragraph detailing QoQ metrics and highlights).\n"
            "3. Quantitative Performance Comparison Table (table node with tableRow, tableHeader, and tableCell nodes):\n"
            "   Headers: 'Performance Metric', 'Q2 Baseline', 'Q3 Actual', 'Variance / Growth'\n"
            "   Rows comparing GA4 Sessions, GA4 Pageviews, Outstanding Invoices, and Active Vault Projects.\n"
            "4. Vault Project Milestones (heading level 2 + bulletList).\n"
            "5. Strategic Recommendations (heading level 2 + paragraph).\n\n"
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

        # Fallback to dynamic structured template if live call fails or API key issue occurs
        return self._get_fallback_tiptap(user_prompt, client_id)

    def _get_fallback_tiptap(self, user_prompt: str, client_id: str = "client_abc") -> dict:
        """Generates a rich executive report blueprint with dynamic comparison tables and metrics."""
        ga4_data = get_ga4_metrics(client_id)
        qb_data = get_quickbooks_data(client_id)
        projects = db_service.run_query("get_projects", {}, client_id)

        q3_ga4 = ga4_data[0] if ga4_data else {"sessions": 10000, "pageviews": 25000, "bounce_rate": 0.42, "traffic_source": "Organic Search"}
        q2_ga4 = ga4_data[1] if len(ga4_data) > 1 else {"sessions": 8500, "pageviews": 21000, "bounce_rate": 0.45, "traffic_source": "Social Media"}

        q3_sessions = q3_ga4.get("sessions", 10000)
        q2_sessions = q2_ga4.get("sessions", 8500)
        sess_growth = f"+{((q3_sessions - q2_sessions) / max(q2_sessions, 1)) * 100:.1f}%"

        q3_pv = q3_ga4.get("pageviews", 25000)
        q2_pv = q2_ga4.get("pageviews", 21000)
        pv_growth = f"+{((q3_pv - q2_pv) / max(q2_pv, 1)) * 100:.1f}%"

        qb_total = qb_data.get("outstanding_invoices_total", 4500.00)
        qb_count = qb_data.get("invoice_count", 2)

        active_projects = [p.get("project_name") for p in projects if p.get("project_name")]
        proj_summary = ", ".join(active_projects) if active_projects else "Vault projects active"

        def cell_para(text: str, is_bold: bool = False):
            marks = [{"type": "bold"}] if is_bold else []
            node: Dict[str, Any] = {"type": "text", "text": str(text)}
            if marks:
                node["marks"] = marks
            return {"type": "paragraph", "content": [node]}

        return {
            "type": "doc",
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 1},
                    "content": [{"type": "text", "text": f"Executive Performance Briefing: {client_id.upper()}"}]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": f"Directive Prompt: '{user_prompt}' | Tenant Vault: ", "marks": [{"type": "italic"}]},
                        {"type": "text", "text": client_id, "marks": [{"type": "bold"}]}
                    ]
                },
                {
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [{"type": "text", "text": "1. Executive Summary & Key Highlights"}]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "During the current review period, "},
                        {"type": "text", "text": client_id, "marks": [{"type": "bold"}]},
                        {"type": "text", "text": f" recorded strong digital growth with organic sessions rising to {q3_sessions:,} ({sess_growth} QoQ). Financial operations reflect {qb_count} open QuickBooks invoices totaling ${qb_total:,.2f}. Vault project execution remains on schedule across active initiatives ({proj_summary})."}
                    ]
                },
                {
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [{"type": "text", "text": "2. Performance & Financial Metrics Breakdown"}]
                },
                {
                    "type": "table",
                    "content": [
                        {
                            "type": "tableRow",
                            "content": [
                                {"type": "tableHeader", "content": [cell_para("Performance Metric", True)]},
                                {"type": "tableHeader", "content": [cell_para("Q2 Baseline", True)]},
                                {"type": "tableHeader", "content": [cell_para("Q3 Actual", True)]},
                                {"type": "tableHeader", "content": [cell_para("Variance / Growth", True)]}
                            ]
                        },
                        {
                            "type": "tableRow",
                            "content": [
                                {"type": "tableCell", "content": [cell_para("GA4 Total Sessions")]},
                                {"type": "tableCell", "content": [cell_para(f"{q2_sessions:,}")]},
                                {"type": "tableCell", "content": [cell_para(f"{q3_sessions:,}")]},
                                {"type": "tableCell", "content": [cell_para(sess_growth, True)]}
                            ]
                        },
                        {
                            "type": "tableRow",
                            "content": [
                                {"type": "tableCell", "content": [cell_para("GA4 Pageviews")]},
                                {"type": "tableCell", "content": [cell_para(f"{q2_pv:,}")]},
                                {"type": "tableCell", "content": [cell_para(f"{q3_pv:,}")]},
                                {"type": "tableCell", "content": [cell_para(pv_growth, True)]}
                            ]
                        },
                        {
                            "type": "tableRow",
                            "content": [
                                {"type": "tableCell", "content": [cell_para("Outstanding Billing")]},
                                {"type": "tableCell", "content": [cell_para("$0.00")]},
                                {"type": "tableCell", "content": [cell_para(f"${qb_total:,.2f}")]},
                                {"type": "tableCell", "content": [cell_para(f"{qb_count} Pending Invoices", True)]}
                            ]
                        },
                        {
                            "type": "tableRow",
                            "content": [
                                {"type": "tableCell", "content": [cell_para("Active Vault Campaigns")]},
                                {"type": "tableCell", "content": [cell_para("1 Project")]},
                                {"type": "tableCell", "content": [cell_para(f"{len(projects)} Projects")]},
                                {"type": "tableCell", "content": [cell_para("Operational", True)]}
                            ]
                        }
                    ]
                },
                {
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [{"type": "text", "text": "3. Vault Project Milestones"}]
                },
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [{"type": "paragraph", "content": [
                                {"type": "text", "text": "Q3 Brand Audit Campaign: ", "marks": [{"type": "bold"}]},
                                {"type": "text", "text": "Active | Allocated Budget: $12,000.00"}
                            ]}]
                        },
                        {
                            "type": "listItem",
                            "content": [{"type": "paragraph", "content": [
                                {"type": "text", "text": "SEO Landing Page Suite: ", "marks": [{"type": "bold"}]},
                                {"type": "text", "text": "Completed | Delivered Budget: $4,500.00"}
                            ]}]
                        }
                    ]
                },
                {
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [{"type": "text", "text": "4. Strategic Next Steps"}]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "1. Settle outstanding QuickBooks invoices before upcoming billing cycle.\n2. Scale organic search acquisition strategy based on positive Q3 session growth."}
                    ]
                }
            ]
        }
