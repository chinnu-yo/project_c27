### 3. `api_contracts.md`

```markdown
# Interface Control Document (`api_contracts.md`)

> **🚨 CRITICAL ARCHITECTURAL DIRECTIVE FOR THE ANTIGRAVITY AGENT:**
> This file serves as the absolute source of truth for all cross-runtime network operations. Whenever a new feature modifies the data architecture or requires structural changes to the data transport layer, you **MUST** update the type contracts and payload schemas in this file **FIRST** before altering any logic in the Next.js frontend or Python backend codebases.

---

## 1. Network Topology & Protocol Contracts

Because the system bridges a **Node.js/TypeScript** frontend runtime environment with a **Python (FastAPI)** orchestration engine, all network contracts are strictly typed and locked down using schema definitions. 

*   **Communication Protocol:** Stateless HTTP REST utilizing validated JSON structures.
*   **Default Ingress Gateway Port (FastAPI Backend):** `http://localhost:8000/api/v1`
*   **Default Content-Type Constraints:** `application/json` for all transmission headers.

---

## 2. Rest Endpoint Contracts & Payload Schemas

### A. Endpoint: `POST /orchestrate`
*   **Description:** Fired from the Next.js workspace canvas view. It triggers the backend compilation sequence: reading local vector preference strings out of ChromaDB, parsing the layout template out of MongoDB, calling the local mock tool functions for data gathering, and generating a clean document layout string.

#### 1. TypeScript Interface Models
```typescript
interface TiptapNode {
  type: string;
  attrs?: Record<string, any>;
  content?: TiptapNode[];
  text?: string;
  marks?: Array<{ type: string; attrs?: Record<string, any> }>;
}

interface OrchestrateRequest {
  client_id: string;      // Unique client identifier (e.g., "client_abc")
  user_prompt: string;    // Raw user intent string (e.g., "Generate the Q3 report")
}

interface OrchestrateResponse {
  status: "success" | "error";
  injected_facts_count: number;
  generated_system_prompt: string;
  tiptap_json: {
    type: "doc";
    content: TiptapNode[];
  };
}
2. Strict Request/Response JSON Examples
Request Payload:

JSON
{
  "client_id": "client_abc",
  "user_prompt": "Generate the Q3 performance report"
}
Response Payload:

JSON
{
  "status": "success",
  "injected_facts_count": 1,
  "generated_system_prompt": "You are an operations compilation agent... Injected Rules: Always use the clean financial layout template...",
  "tiptap_json": {
    "type": "doc",
    "content": [
      {
        "type": "heading",
        "attrs": { "level": 1 },
        "content": [{ "type": "text", "text": "Q3 Performance Review" }]
      }
    ]
  }
}
B. Endpoint: POST /memory/validate
Description: Fired when an account manager interacts with the Fact Validation panel to approve or reject a preference string extracted by the background AI Critic task.

1. TypeScript Interface Models
TypeScript
interface MemoryValidateRequest {
  notification_id: string;                // The MongoDB document tracking ID
  client_id: string;                      // Enforces strict tenant separation
  action: "approve" | "reject";          // Action boundary logic
  extracted_fact: string;                 // The distilled sentence to embed if approved
  domain: "formatting_preference" | "accounting_logic" | "metric_definitions";
}

interface MemoryValidateResponse {
  status: "success";
  notification_id: string;
  current_state: "approved" | "rejected";
  chroma_id?: string;                     // Provided if injected into vector layer
}
2. Strict Request/Response JSON Examples
Request Payload:

JSON
{
  "notification_id": "notif_99b12d45",
  "client_id": "client_abc",
  "action": "approve",
  "extracted_fact": "Always use the clean financial layout template for client_abc corporate reporting.",
  "domain": "formatting_preference"
}
Response Payload:

JSON
{
  "status": "success",
  "notification_id": "notif_99b12d45",
  "current_state": "approved",
  "chroma_id": "mem_09f83a21"
}
C. Endpoint: POST /reports/save
1. TypeScript Interface Models
TypeScript
interface SaveReportRequest {
  client_id: string;
  report_name: string;
  tiptap_json: {
    type: "doc";
    content: TiptapNode[];
  };
}

interface SaveReportResponse {
  status: "success";
  report_id: string;
  saved_at: number;
}
Request Payload:

JSON
{
  "client_id": "client_abc",
  "report_name": "Q3 Final Executive Brief",
  "tiptap_json": {
    "type": "doc",
    "content": [
      {
        "type": "heading",
        "attrs": { "level": 1 },
        "content": [{ "type": "text", "text": "Q3 Final Executive Brief" }]
      }
    ]
  }
}
D. Endpoint: POST /search
Description: Global cross-app natural language command bar search endpoint. Queries internal mock functions and returns synthesized analysis details.

1. TypeScript Interface Models
TypeScript
interface CrossAppSearchRequest {
  client_id: string;
  query_string: string;
}

interface CrossAppSearchResponse {
  status: "success";
  answer: string;
  sources_consulted: string[]; 
}
Request Payload:

JSON
{
  "client_id": "client_abc",
  "query_string": "What was our GA4 traffic compared to outstanding invoices this month?"
}
Response Payload:

JSON
{
  "status": "success",
  "answer": "For client_abc this month, GA4 traffic recorded 10,000 sessions while outstanding QuickBooks invoices total $4,500 across two accounts.",
  "sources_consulted": ["ga4", "quickbooks"]
}
3. Python Backend Validation Structures (FastAPI Models)
To keep backend logic synchronized with these validation boundaries, FastAPI uses the following matching Pydantic schema definitions:

Python
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

class TiptapNodeModel(BaseModel):
    type: str
    attrs: Optional[Dict[str, Any]] = None
    content: Optional[List['TiptapNodeModel']] = None
    text: Optional[str] = None
    marks: Optional[List[Dict[str, Any]]] = None

class TiptapDocContainer(BaseModel):
    type: Literal["doc"]
    content: List[TiptapNodeModel]

# Endpoint Schema Mappings
class OrchestrateRequestModel(BaseModel):
    client_id: str
    user_prompt: str

class OrchestrateResponseModel(BaseModel):
    status: Literal["success", "error"]
    injected_facts_count: int
    generated_system_prompt: str
    tiptap_json: TiptapDocContainer

class MemoryValidateRequestModel(BaseModel):
    notification_id: str
    client_id: str
    action: Literal["approve", "reject"]
    extracted_fact: str
    domain: Literal["formatting_preference", "accounting_logic", "metric_definitions"]

class MemoryValidateResponseModel(BaseModel):
    status: Literal["success"]
    notification_id: str
    current_state: Literal["approved", "rejected"]
    chroma_id: Optional[str] = None

class SaveReportRequestModel(BaseModel):
    client_id: str
    report_name: str
    tiptap_json: TiptapDocContainer

class SaveReportResponseModel(BaseModel):
    status: Literal["success"]
    report_id: str
    saved_at: int

class CrossAppSearchRequestModel(BaseModel):
    client_id: str
    query_string: str

class CrossAppSearchResponseModel(BaseModel):
    status: Literal["success"]
    answer: str
    sources_consulted: List[str]

class LoginRequestModel(BaseModel):
    client_id: str
    password: str

class LoginResponseModel(BaseModel):
    access_token: str
    token_type: str = "bearer"
    client_id: str