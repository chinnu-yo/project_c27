### 2. `system_architecture.md`

```markdown
# System Architecture Document (`system_architecture.md`)

## 1. Structural Component Ecosystem Overview

The application architecture utilizes a clean decoupling of layout styling from processing loops. The system operates across three core execution lanes: a responsive web application frame (**Next.js**, utilizing the stable *App Router* paradigm on React 18), a dynamic async orchestrator layer (**FastAPI**), and an optimized local vector index engine (**ChromaDB** running entirely offline via CPU embeddings).

---

## 2. Next.js Frontend Layer (Client-Side Workspace)

### A. UI Routing Blueprint
Using the Next.js App Router, the application workspace enforces strict separation between system admin tools and user client dashboards:
```text
src/app/
├── (auth)/
│   └── login/page.tsx               # Workspace session ingress
├── (dashboard)/
│   ├── layout.tsx                   # Central Shell containing sidebar navigation
│   ├── page.tsx                    # Command search box & quick stats panel
│   ├── memory/
│   │   └── page.tsx                 # Fact Validation notification log center
│   └── workspace/
│       └── [client_id]/
│           └── page.tsx             # Interactive Side-by-Side Canvas view
B. Client-Side State Management & Version Locks
React 18 Architecture: Pinned strictly to React 18 base configurations to maintain clean compatibility across all deep Tiptap extension nodes and prevent npm ERR! code ERESOLVE installer flags.

Global Workspace State: Managed via a lightweight Zustand store to keep track of the currently selected client_id and active connection tokens.

Document Canvas State: Managed natively by the Tiptap Editor React Hook Engine.

3. Python Backend Layer (FastAPI Application Host)
A. API Routing Framework Architecture
FastAPI handles incoming data traffic through strict Pydantic validation parameters:

/api/v1/orchestrate: Receives the query string, triggers vector search, routes local functional tools, and returns the compiled Tiptap schema payload.

/api/v1/memory/validate: Handles human-in-the-loop transition logic, updating a verified fact from MongoDB and indexing it into ChromaDB.

B. The Agentic Orchestration Lifecycle Service
The orchestrator endpoint manages the execution flow asynchronously using local processing structures and built-in background task handlers:

Python
# backend/app/services/orchestrator.py
from fastapi import BackgroundTasks

class OrchestrationEngine:
    def __init__(self, chroma_client, mongo_client, local_tools):
        self.chroma = chroma_client
        self.mongo = mongo_client
        self.tools = local_tools

    async def execute_workflow(self, client_id: str, raw_user_prompt: str, background_tasks: BackgroundTasks) -> dict:
        # Step 1: Query local vector space for semantic formatting rules
        historical_context = await self.chroma.retrieve_client_facts(client_id, query=raw_user_prompt)
        
        # Step 2: Grab layout template configurations from MongoDB Atlas
        base_blueprint = await self.mongo.db.report_templates.find_one({"client_id": client_id})
        
        # Step 3: Run local tool compilation loop and call LLM context block
        compiled_tiptap_json = await self.tools.execute_in_app_loop(
            user_prompt=raw_user_prompt,
            context=historical_context,
            blueprint=base_blueprint
        )
        
        # Step 4: Dispatch the AI Critic using native FastAPI BackgroundTasks
        # This keeps the user dashboard fast and lag-free without needing Celery/Redis
        background_tasks.add_task(self.tools.run_async_critic, client_id, compiled_tiptap_json)
        
        return compiled_tiptap_json
4. Vector Storage Layer (ChromaDB Local Core Memory)
A. Collection Schema Configuration
The vector space uses a single dedicated collection name. It uses metadata parameters to enforce multi-tenancy constraints:

Collection Reference Name: client_contextual_memory

System Vector Record Shape:

Embedding Vector: Array of 384 floating-point values.

Document Value: Clean plain-text statement (e.g., "Always format quarterly tables matching the finance layout rules.").

B. Mathematical Distance Metric Specifics
The system uses the Cosine Similarity Metric (cosine) to calculate vector distance inside the engine index.

C. Embedding Model Engine Specifications (100% Local CPU)
To completely cut out OpenAI embedding token costs and maintain absolute data privacy, generation is offloaded entirely to local compute:

Target Engine Model: all-MiniLM-L6-v2 via native Chroma embedding functions.

Vector Dims Layer: 384 dimensions.

Execution Strategy: On first execution, the local wrapper downloads model weights down to your host device. All subsequent textual mappings run locally on your CPU with zero network dependencies.

Python
# backend/app/services/chroma_service.py
import chromadb
from chromadb.utils import embedding_functions

class ChromaMemoryLayer:
    def __init__(self, persist_path="./chroma_data"):
        self.client = chromadb.PersistentClient(path=persist_path)
        # Bypasses cloud keys. Uses native local computing layer.
        self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name="client_contextual_memory",
            embedding_function=self.emb_fn,
            metadata={"hnsw:space": "cosine"}
        )

    async def retrieve_client_facts(self, client_id: str, query: str) -> list:
        results = self.collection.query(
            query_texts=[query],
            n_results=2,
            where={"client_id": client_id} # The absolute database multi-tenancy guardrail
        )
        if not results or not results.get('documents') or not results['documents'][0]:
            return []
        return results['documents'][0]