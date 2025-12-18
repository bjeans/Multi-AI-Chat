from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from models.schemas import CouncilDebateRequest
from services.orchestrator import CouncilOrchestrator

router = APIRouter(prefix="/api/council", tags=["council"])


@router.post("/debate")
async def council_debate(request: CouncilDebateRequest):
    """
    Start a council debate with streaming responses
    Returns Server-Sent Events stream
    """
    orchestrator = CouncilOrchestrator()

    # Convert MCP config to dict if provided
    mcp_config = None
    if request.mcp_config:
        mcp_config = {
            "enabled": request.mcp_config.enabled,
            "server_labels": request.mcp_config.server_labels,
            "allowed_tools": request.mcp_config.allowed_tools,
        }

    async def event_generator():
        async for event in orchestrator.run_council_debate(
            query=request.query,
            council_members=request.council_members,
            chairman=request.chairman,
            mcp_config=mcp_config,
        ):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
