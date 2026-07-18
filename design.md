# System Design Document (`design.md`)

## 1. System Topology & Data Flow Architectures

The platform utilizes a structured, human-in-the-loop agentic pattern. **FastAPI** serves as the central orchestration engine, mediating communication between the **Next.js frontend core**, external API mock layers, transactional storage (**MongoDB Atlas**), and the local contextual memory space (**ChromaDB**).

                             +----------------------------------+
                             |   Next.js Frontend Dashboard    |
                             +----------------------------------+
                                       ^               |
                 Rendered Tiptap JSON  |               |  1. "Run Q3 Report"
                 Canvas Data Payloads  |               |  User Operations
                                       |               v
                             +----------------------------------+
                             |    FastAPI Execution Core        |
                             +----------------------------------+
                              /         |             |        \
                             /          |             |         \
     2. Read Schema Blueprint/          |             |          \ 3. Local Semantic Search
               Audit Metadata           |             |           \    Metadata Isolation
                           v            |             |            v
           +-------------------+        |             |      +--------------------+
           |   MongoDB Atlas   |        |             |      | ChromaDB Instance  |
           | (M0 Free Cloud)   |        |             |      | (Sentence-Transf.) |
           +-------------------+        |             |      +--------------------+
                                        v             v
                          +------------------+   +-------------------+
                          | External/Remote  |   | Lightweight In-App|
                          |   Mock Scripts   |   |   Local Functions |
                          +------------------+   +-------------------+
                          | - HubSpot SSE    |   | - GA4 Mock Fn     |
                          |   Proxy Wrapper  |   | - QuickBooks Fn   |
                          |                  |   | - SQLite Local File|
                          +------------------+   +-------------------+

---

## 2. Multi-Tenant Database Pillar Specifications

To balance low latency, zero cloud cost token overhead, and strict tenant security, data storage is segmented across four separate execution frameworks.

### Pillar 1: Vector Contextual Learnings (ChromaDB + Local Sentence-Transformers)
*   **Infrastructure Layout:** Self-hosted open-source `PersistentClient` targeting a dedicated local folder directory, powered by a native, local `all-MiniLM-L6-v2` execution wrapper.
*   **Logical Execution:** Houses declarative sentences describing learned behavioral preferences extracted by the native FastAPI `BackgroundTasks` AI Critic service.
*   **Strict Multi-Tenancy Boundary:** Vector proximity matching (`collection.query`) *must* inject an explicit metadata constraint filter matching the session `client_id`. This prevents cross-tenant data leaks.
*   **Data Model Spec:**
```json
{
  "id": "mem_09f83a21",
  "document": "Always use the clean financial layout template for client_abc corporate reporting.",
  "metadata": {
    "client_id": "client_abc",
    "domain": "formatting_preference",
    "timestamp": 1774845021,
    "confidence_score": 0.95
  }
}
Pillar 2: Transactional & Structural Records (MongoDB Atlas)
Infrastructure Layout: Permanently Free Tier (M0 Cluster Container) cloud engine.

Logical Execution: Maintains operational system states, user records, analytical dashboard notifications, and structural document layout frameworks.

Data Model Spec (report_templates):

JSON
{
  "_id": "tmpl_9918bc",
  "client_id": "firm_xyz",
  "template_name": "Executive Quarterly Report",
  "tiptap_schema_blueprint": {
    "type": "doc",
    "content": [
      { "type": "heading", "attrs": { "level": 1 }, "content": [{ "type": "text", "text": "{{COMPANY_NAME}} Performance Review" }] },
      { "type": "paragraph", "content": [{ "type": "text", "text": "Reporting Period: {{REPORTING_PERIOD}}" }] },
      { "type": "data_component_block", "attrs": { "source": "hubspot", "metrics": ["deals_closed"] } },
      { "type": "heading", "attrs": { "level": 2 }, "content": [{ "type": "text", "text": "Executive Analytical Summary" }] },
      { "type": "ai_generation_block", "attrs": { "prompt_guideline": "Formal tone." } }
    ]
  }
}
Pillar 3: Real-Time Operational Interfaces (Lightweight Tool Functions)
Infrastructure Layout: Decoupled, local standard Python functions running inside the main execution container to eliminate subprocess networking friction.

HubSpot Mock: Connected via a lightweight local SSE endpoint mimicking CRM lifecycle pipelines.

GA4 & QuickBooks Mocks: Standard Python modules parsing static mock JSON arrays for sandbox isolation.

Internal Client DB: Native SQLite single-file connector (client_vault.db) running with zero background database servers and protected by a read-only tools.yaml logic query map.

Pillar 4: Interactive Web UI Layout (Tiptap Document Nodes)
Infrastructure Layout: Frontend component library running on Next.js 14/15 + React 18 for completely stable package peer matching.

Logical Execution: Renders the generative AI output visually on the client dashboard interface using standard HTML/CSS text sheets. The document handles edits natively inside the browser window, making a standard HTTP API save request only when explicitly instructed.

3. Dynamic Runtime Orchestration & Code Execution Loop
+-----------------------------------+
|  1. FastAPI Ingress & Intercept   |
+-----------------------------------+
                  | 
                  v Map Active Session Data
+-----------------------------------+
| 2. Context Ingestion Stage        |
| - Pull rules from ChromaDB        |
| - Pull blueprints from MongoDB    |
+-----------------------------------+
                  |
                  v Build System Directives & Deliver to LLM Engine
+-----------------------------------+
| 3. Agentic Intention Stage        |
| - LLM reads local in-app tools    |
| - Emits function call blocks      |
+-----------------------------------+
                  |
                  v Intercept Request Execution Actions
+-----------------------------------+
| 4. Lightweight Native Extraction  |
| - Queries local files & tools     |
| - Reads single-file SQLite tables |
+-----------------------------------+
                  |
                  v Feed JSON Metric Variables Back into Context Pool
+-----------------------------------+
| 5. Core Synthesis Stage           |
| - LLM generates structural tree   |
| - Outputs clean Tiptap JSON       |
+-----------------------------------+
4. Systems Security Matrix & Access Controls
A. Zero-Trust Tool Constraints
OAuth 2.1 Ingress Tokenization: Session authentication handles connection tracking via short-lived tokens. Database file pathways are never exposed to the client.

Context Injection Shield: All streaming payloads extracted via local mock modules are parsed through strict backend validation schemas before reaching the model engine.

B. Human-in-the-Loop Memory Isolation Moat
Write Boundary Safeguards: The automated core engine operates with completely read-only system scopes. State transformations across mock CRM platforms or SQLite tables cannot execute directly from text generation loops.

Validation Verification Loop: The FastAPI native BackgroundTasks thread processes document changes without blocking user interfaces. It places new findings into a pending_approval state in MongoDB. The facts are written to the local ChromaDB vector layer only after a human supervisor clicks [Approve Preference] on the Next.js web application dashboard.