from fastapi import BackgroundTasks
from backend.app.services.chroma_service import ChromaMemoryLayer
from backend.app.services.mongo_service import MongoService
from backend.app.services.local_tools import LocalToolsManager
from backend.app.services.critic_service import CriticService

class OrchestrationEngine:
    def __init__(
        self,
        chroma_client: ChromaMemoryLayer,
        mongo_client: MongoService,
        local_tools: LocalToolsManager,
        critic_service: CriticService
    ):
        self.chroma = chroma_client
        self.mongo = mongo_client
        self.tools = local_tools
        self.critic = critic_service

    async def execute_workflow(
        self,
        client_id: str,
        raw_user_prompt: str,
        background_tasks: BackgroundTasks
    ) -> dict:
        """Coordinates retrieval of constraints, calls generation suite, and triggers background Critic review."""
        
        # Step 1: Query local vector space for semantic formatting rules
        historical_context = await self.chroma.retrieve_client_facts(
            client_id=client_id,
            query=raw_user_prompt
        )
        
        # Step 2: Grab layout template configurations from MongoDB Atlas
        base_blueprint = self.mongo.get_template(client_id=client_id)
        if not base_blueprint:
            base_blueprint = self.mongo._get_fallback_template(client_id=client_id)
        
        # Step 3: Run local tool compilation loop and call LLM context block
        compiled_tiptap_json = await self.tools.execute_in_app_loop(
            user_prompt=raw_user_prompt,
            context=historical_context,
            blueprint=base_blueprint
        )
        
        # Step 4: Dispatch the AI Critic using native FastAPI BackgroundTasks
        # This keeps user dashboard fast and lag-free without Celery/Redis
        background_tasks.add_task(
            self.critic.run_async_critic,
            client_id,
            compiled_tiptap_json
        )
        
        return compiled_tiptap_json
