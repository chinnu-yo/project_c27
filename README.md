# Agentic Workspace System of Action

A production-ready multi-tenant Agentic System of Action for mid-market professional services.

## Architecture Outline
- **Frontend**: Next.js 14 (App Router) + React 18 + Zustand 4 + Tiptap Editor Canvas.
- **Backend**: FastAPI (Python 3.11+) orchestration gateway.
- **Local Contextual Memory**: ChromaDB offline CPU embeddings using Sentence-Transformers (`all-MiniLM-L6-v2`).
- **Client Relational Vault**: SQLite single-file database (`client_vault.db`) constrained by `tools.yaml` query mapping.
- **Transactional DB**: MongoDB Atlas.
- **AI Engine**: Google Gemini API (via `google-generativeai` SDK).

## Running the Application
Detailed run commands will be populated during system integration.

<h2>Screenshots</h2>

<p align="center">
<h4>Login page</h4><br>
  <img src="screenshots/Login_page.png" width="800"><br><br>

  <h4>Dashboard</h4><br>
  <img src="screenshots/Dashboard Hub.png" width="800"><br><br>
  
  <h4>Client Templates</h4><br>
  <img src="screenshots/Templates.png" width="800"><br><br>

  <h4>Report generator</h4><br>
  <img src="screenshots/Report generator.png" width="800"><br><br>

  <h4>intigrations settings</h4><br>
  <img src="screenshots/Intigrations settings.png" width="800">

  <h4>Team and access management</h4><br>
  <img src="screenshots/Team_and_access.png" width="800">
</p>