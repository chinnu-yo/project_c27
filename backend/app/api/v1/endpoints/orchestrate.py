from fastapi import APIRouter, Depends, BackgroundTasks
from backend.app.api.dependencies import get_orchestrator
from backend.app.services.orchestrator import OrchestrationEngine
from backend.app.schemas.orchestrate_schemas import OrchestrateRequestModel, OrchestrateResponseModel

router = APIRouter()

@router.post("/orchestrate", response_model=OrchestrateResponseModel)
async def orchestrate_report(
    payload: OrchestrateRequestModel,
    background_tasks: BackgroundTasks,
    engine: OrchestrationEngine = Depends(get_orchestrator)
):
    """Triggers report compilation, reads vector limits, and registers async Critic loops."""
    try:
        # Step 1 & 2 & 3: Run retrieval and tool synthesis via Orchestrator
        tiptap_out = await engine.execute_workflow(
            client_id=payload.client_id,
            raw_user_prompt=payload.user_prompt,
            background_tasks=background_tasks
        )

        # Retrieve count of rules dynamically from chroma
        facts = await engine.chroma.retrieve_client_facts(payload.client_id, payload.user_prompt)

        return OrchestrateResponseModel(
            status="success",
            injected_facts_count=len(facts),
            generated_system_prompt=f"System compiler active. Applied rules: {', '.join(facts)}",
            tiptap_json=tiptap_out
        )
    except Exception as e:
        return OrchestrateResponseModel(
            status="error",
            injected_facts_count=0,
            generated_system_prompt=f"Orchestration failure: {str(e)}",
            tiptap_json={"type": "doc", "content": [
                {"type": "heading", "attrs": {"level": 1}, "content": [{"type": "text", "text": "Generation Failure"}]},
                {"type": "paragraph", "content": [{"type": "text", "text": f"Error occurred: {str(e)}"}]}
            ]}
        )
