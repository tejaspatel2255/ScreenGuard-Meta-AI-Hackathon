from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.core.procedure_parser import parse_procedure_service
from backend.app.core.session import session_store
from backend.app.core.step_engine import Event, StepStateType
from backend.app.model_clients.base import ProcedureParseResult, ProcedureStep
from backend.app.model_clients.factory import get_model_client

router = APIRouter(prefix="/api", tags=["screenguard"])


class ParseRequest(BaseModel):
    text: str


class SessionStartRequest(BaseModel):
    procedure: ProcedureParseResult


class SessionStartResponse(BaseModel):
    session_id: str
    steps: List[ProcedureStep]
    states: Dict[str, StepStateType]
    current_step_id: Optional[str]


class SessionDetailResponse(BaseModel):
    session_id: str
    states: Dict[str, StepStateType]
    current_step_id: Optional[str]
    progress: Dict[str, int]
    is_complete: bool
    events: List[Event]


class OverrideRequest(BaseModel):
    step_id: str
    state: StepStateType


@router.post("/procedure/parse", response_model=ProcedureParseResult)
async def parse_procedure_endpoint(req: ParseRequest) -> ProcedureParseResult:
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Procedure text cannot be empty.")
    client = get_model_client()
    return await parse_procedure_service(req.text, client)


@router.post("/session/start", response_model=SessionStartResponse)
async def start_session_endpoint(req: SessionStartRequest) -> SessionStartResponse:
    if not req.procedure.steps:
        raise HTTPException(status_code=400, detail="Procedure must have at least one step.")

    session = await session_store.create_session(req.procedure)
    return SessionStartResponse(
        session_id=session.id,
        steps=session.procedure.steps,
        states=session.engine.states,
        current_step_id=session.engine.current_step_id,
    )


@router.get("/session/{session_id}", response_model=SessionDetailResponse)
async def get_session_endpoint(session_id: str) -> SessionDetailResponse:
    session = await session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    return SessionDetailResponse(
        session_id=session.id,
        states=session.engine.states,
        current_step_id=session.engine.current_step_id,
        progress=session.engine.progress,
        is_complete=session.engine.is_complete,
        events=session.engine.events,
    )


@router.post("/session/{session_id}/override", response_model=SessionDetailResponse)
async def override_session_endpoint(session_id: str, req: OverrideRequest) -> SessionDetailResponse:
    session = await session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    try:
        session.engine.override(req.step_id, req.state)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return SessionDetailResponse(
        session_id=session.id,
        states=session.engine.states,
        current_step_id=session.engine.current_step_id,
        progress=session.engine.progress,
        is_complete=session.engine.is_complete,
        events=session.engine.events,
    )


@router.post("/session/{session_id}/restart", response_model=SessionDetailResponse)
async def restart_session_endpoint(session_id: str) -> SessionDetailResponse:
    session = await session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    session.engine.restart()
    return SessionDetailResponse(
        session_id=session.id,
        states=session.engine.states,
        current_step_id=session.engine.current_step_id,
        progress=session.engine.progress,
        is_complete=session.engine.is_complete,
        events=session.engine.events,
    )


@router.get("/budget")
async def get_budget_endpoint() -> Dict[str, Any]:
    client = get_model_client()
    if hasattr(client, "usage"):
        return client.usage()
    return {
        "calls_total": 0,
        "calls_this_minute": 0,
        "estimated_spend_usd": 0.0,
        "spend_limit_usd": 100.0,
    }
