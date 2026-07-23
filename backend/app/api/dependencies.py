from backend.app.services.mongo_service import MongoService
from backend.app.services.chroma_service import ChromaMemoryLayer
from backend.app.services.local_tools import LocalToolsManager
from backend.app.services.critic_service import CriticService
from backend.app.services.orchestrator import OrchestrationEngine

# Shared singleton dependencies across the backend gateway instance
mongo_db = MongoService()
chroma_db = ChromaMemoryLayer()
tools_mgr = LocalToolsManager()
critic_mgr = CriticService()

engine = OrchestrationEngine(
    chroma_client=chroma_db,
    mongo_client=mongo_db,
    local_tools=tools_mgr,
    critic_service=critic_mgr
)

def get_mongo_service() -> MongoService:
    return mongo_db

def get_chroma_service() -> ChromaMemoryLayer:
    return chroma_db

def get_orchestrator() -> OrchestrationEngine:
    return engine
