import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.core.step_engine import Event, StepEngine, StepStateType
from backend.app.model_clients.base import ProcedureParseResult, ProcedureStep


class Session(BaseModel):
    id: str
    procedure: ProcedureParseResult
    engine: StepEngine
    events: List[Event] = Field(default_factory=list)
    trace: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    calls_used: int = 0

    model_config = {"arbitrary_types_allowed": True}


class SessionStore:
    """Thread-safe in-memory session store."""

    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}
        self._lock = asyncio.Lock()

    async def create_session(self, procedure: ProcedureParseResult) -> Session:
        async with self._lock:
            session_id = f"sess-{uuid.uuid4().hex[:8]}"
            engine = StepEngine(procedure.steps)
            session = Session(
                id=session_id,
                procedure=procedure,
                engine=engine,
                events=[],
                trace=[],
                created_at=time.time(),
            )
            self._sessions[session_id] = session
            return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        async with self._lock:
            return self._sessions.get(session_id)

    async def delete_session(self, session_id: str) -> bool:
        async with self._lock:
            return self._sessions.pop(session_id, None) is not None


session_store = SessionStore()
