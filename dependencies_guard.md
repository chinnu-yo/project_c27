### 4. `dependency_guard.md`

```markdown
# Dependency Management Protocol (`dependency_guard.md`)

> **🚨 CRITICAL OPERATIONS RULE FOR THE ANTIGRAVITY AGENT:**
> The agent shall not install, remove, or update any package, library, or system dependency without explicit, line-by-line human approval in the chat. Do not automate package manager updates or modify lockfiles autonomously.

---

## 1. Node.js/TypeScript Ingress Framework (Frontend Environment)

To guarantee that visual layout logic, component hierarchies, and text editors never break due to downstream version mismatches, the frontend runtime environment is strictly pinned to React 18 configuration spaces to secure stable Tiptap compilation bounds.

### A. Critical Package Dependencies (`package.json`)
The following structural packages are pinned. Do not upgrade these minor or major versions, as Tiptap extensions rely on strict peer dependencies with the core ProseMirror engine.

```json
{
  "dependencies": {
    "next": "14.2.5",
    "react": "18.3.1",
    "react-dom": "18.3.1",
    "@tiptap/react": "2.10.3",
    "@tiptap/pm": "2.10.3",
    "@tiptap/starter-kit": "2.10.3",
    "@tiptap/extension-table": "2.10.3",
    "@tiptap/extension-table-row": "2.10.3",
    "@tiptap/extension-table-cell": "2.10.3",
    "zustand": "4.5.4"
  }
}
B. Verification Blueprint
Enforcement Command: Every local build or integration check must execute package installations via npm ci (Clean Install) rather than a loose npm install.

Lockfile Status: package-lock.json is signed, versioned, and treated as read-only.

2. Python Orchestration Engine Framework (Backend Environment)
A. Core Requirements Specification (requirements.txt)
These specific versions are locked to protect database query operations, local vector calculation models, and in-app system wrappers:

Plaintext
# Server Gateway Ingress Engine
fastapi==0.111.0
uvicorn==0.51.0
pydantic==2.7.4

# Storage & Local Vector Moat Layer
chromadb==1.5.9
pymongo==4.7.3
sentence-transformers==3.0.1

# Core Agent Coordination Architecture
google-antigravity==0.1.7

# Computational Utilities & Network Connectors
google-generativeai==0.7.2
httpx==0.27.0
python-dotenv==1.0.1
B. System Constraints & Conflicts Matrix
ChromaDB Local Vector Engine: chromadb relies on local compilation steps for computing vector maps. The agent is strictly banned from modifying this version line to prevent host runtime machine build breakages.

Pydantic Data Integration: FastAPI uses Pydantic V2 schemas for interface controls. The agent must verify that all database entities and tool schemas are written using the V2 namespace definitions (from pydantic import BaseModel), never falling back to V1 legacy structures.

3. Dependency Integrity Verification Protocol
Before writing logic blocks or modifying endpoint schemas, the coding agent must run this verification checklist to ensure alignment with the system setup:

Plaintext
                    INTEGRITY CHECKLIST
┌────────────────────────────────────────────────────────┐
│ 1. Validate lockfiles remain unmodified                │
├────────────────────────────────────────────────────────┤
│ 2. Ensure all text nodes map to Tiptap 2.10 specs      │
├────────────────────────────────────────────────────────┤
│ 3. Match Pydantic models with api_contracts.md schemas │
└────────────────────────────────────────────────────────┘