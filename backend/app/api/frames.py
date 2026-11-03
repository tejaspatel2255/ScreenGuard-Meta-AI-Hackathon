from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Request, Response
from backend.app.core.agent import AgentLoop, StepUpdate
from backend.app.core.session import session_store
from backend.app.model_clients.factory import get_model_client

router = APIRouter(prefix="/api", tags=["frames"])

_agent_loop: AgentLoop | None = None


def get_agent_loop() -> AgentLoop:
    global _agent_loop
    if _agent_loop is None:
        client = get_model_client()
        _agent_loop = AgentLoop(client)
    return _agent_loop


@router.post("/session/{session_id}/frame", response_model=StepUpdate)
async def process_frame_endpoint(session_id: str, request: Request) -> StepUpdate:
    session = await session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    content_type = request.headers.get("content-type", "").lower()
    if not any(t in content_type for t in ["image/jpeg", "image/png", "application/octet-stream"]):
        raise HTTPException(status_code=415, detail="Unsupported media type. Body must be image/jpeg or image/png.")

    body = await request.body()

    # Limit to 1.5 MB
    if len(body) > 1.5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Payload Too Large. Frame exceeds 1.5 MB limit.")

    if not body:
        raise HTTPException(status_code=415, detail="Empty frame body.")

    agent_loop = get_agent_loop()
    try:
        return await agent_loop.process(session, body)
    except ValueError as e:
        raise HTTPException(status_code=415, detail=str(e))
    except Exception as e:
        if "budget" in str(e).lower() or "spend" in str(e).lower():
            raise HTTPException(status_code=429, detail=f"Budget limit reached: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/trace")
async def get_session_trace_endpoint(session_id: str) -> List[Dict[str, Any]]:
    session = await session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return session.trace
