import asyncio
import io
import time
from typing import Any, Dict, List, Optional
from PIL import Image
import pytest
from fastapi.testclient import TestClient

from backend.app.core.agent import Action, AgentLoop, StepUpdate
from backend.app.core.policy import AgentPolicy
from backend.app.core.session import Session, session_store
from backend.app.core.step_engine import StepEngine
from backend.app.main import app
from backend.app.model_clients.base import (
    BoundingBox,
    ExportResult,
    LocateElementsResult,
    ModelClient,
    ProcedureParseResult,
    ProcedureStep,
    TranscriptionResult,
    VerdictResult,
)
from backend.app.model_clients.spend_guard import SpendLimitReached


def create_dummy_png(color=(73, 109, 137), size=(400, 300)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class ScriptedFakeClient(ModelClient):
    """Deterministic client returning scripted verdicts for agent testing."""

    def __init__(self, verdicts: Optional[List[VerdictResult]] = None, fail_sam: bool = False, raise_spend: bool = False) -> None:
        self.verdicts = verdicts or []
        self.fail_sam = fail_sam
        self.raise_spend = raise_spend
        self.call_count = 0

    async def parse_procedure(self, text: str) -> ProcedureParseResult:
        return ProcedureParseResult(title="Test", steps=[], source="mock")

    async def judge_frame(self, image_bytes: bytes, step: ProcedureStep, context: Dict[str, Any]) -> VerdictResult:
        if self.raise_spend:
            raise SpendLimitReached("Max spend hit")
        self.call_count += 1
        if self.verdicts:
            idx = min(self.call_count - 1, len(self.verdicts) - 1)
            return self.verdicts[idx]
        return VerdictResult(step_id=step.id, status="done", observed_step_ids=[step.id], evidence="OK", confidence=0.9, source="mock")

    async def locate_elements(self, image_bytes: bytes, prompts: List[str]) -> LocateElementsResult:
        if self.fail_sam:
            raise RuntimeError("SAM inference failed")
        return LocateElementsResult(elements=[BoundingBox(label="Btn", box_2d=[0, 0, 0.1, 0.1], confidence=0.9)], source="mock")

    async def transcribe_audio(self, audio_bytes: bytes) -> TranscriptionResult:
        return TranscriptionResult(text="", source="mock")

    async def generate_export(self, procedure: ProcedureParseResult) -> ExportResult:
        return ExportResult(formatted_document="", source="mock")

    def usage(self) -> Dict[str, Any]:
        return {"calls_total": self.call_count, "estimated_spend_usd": 0.001, "spend_limit_usd": 100.0}

    def model_info(self) -> Dict[str, str]:
        return {"provider": "mock", "vision_model": "scripted-vision", "text_model": "scripted-text", "family": "mock"}


def create_test_session():
    steps = [
        ProcedureStep(id="step-1", order=1, instruction="Login", success_condition="Dashboard open", risk="low"),
        ProcedureStep(id="step-2", order=2, instruction="Select Damaged", success_condition="Selected", risk="low"),
        ProcedureStep(id="step-3", order=3, instruction="Authorize refund", success_condition="Approved", risk="high"),
    ]
    proc = ProcedureParseResult(title="Test Flow", steps=steps, source="mock")
    engine = StepEngine(steps)
    return Session(id="test-sess-1", procedure=proc, engine=engine)


# 1. Advance on done with high confidence
def test_agent_advance():
    verdict = VerdictResult(step_id="step-1", status="done", observed_step_ids=["step-1"], evidence="Visible", confidence=0.85, source="mock")
    client = ScriptedFakeClient(verdicts=[verdict])
    loop = AgentLoop(client)
    sess = create_test_session()

    update = asyncio.run(loop.process(sess, create_dummy_png()))
    assert update.action == Action.ADVANCE
    assert sess.engine.states["step-1"] == "done"
    assert update.current_step_id == "step-2"


# 2. Wait on in_progress
def test_agent_wait_in_progress():
    verdict = VerdictResult(step_id="step-1", status="in_progress", observed_step_ids=["step-1"], evidence="Typing", confidence=0.9, source="mock")
    client = ScriptedFakeClient(verdicts=[verdict])
    loop = AgentLoop(client)
    sess = create_test_session()

    update = asyncio.run(loop.process(sess, create_dummy_png()))
    assert update.action == Action.WAIT
    assert sess.engine.states["step-1"] == "active"


# 3. Warn on low-risk wrong
def test_agent_warn_low_risk_wrong():
    verdict = VerdictResult(step_id="step-1", status="wrong", observed_step_ids=["step-1"], evidence="Wrong field", warning_text="Fix username", confidence=0.95, source="mock")
    client = ScriptedFakeClient(verdicts=[verdict])
    loop = AgentLoop(client)
    sess = create_test_session()

    update = asyncio.run(loop.process(sess, create_dummy_png()))
    assert update.action == Action.WARN
    assert update.blocking is False
    assert "Fix username" in (update.warning or "")


# 4. Stop on high-risk wrong
def test_agent_stop_high_risk_wrong():
    verdict = VerdictResult(step_id="step-3", status="wrong", observed_step_ids=["step-3"], evidence="Unauthorized submit", warning_text="Stop unauthorized submission", confidence=0.95, source="mock")
    client = ScriptedFakeClient(verdicts=[verdict])
    loop = AgentLoop(client)
    sess = create_test_session()
    sess.engine.override("step-1", "done")
    sess.engine.override("step-2", "done")

    update = asyncio.run(loop.process(sess, create_dummy_png()))
    assert update.action == Action.STOP
    assert update.blocking is True


# 5. Skip detection triggers warning/stop
def test_agent_skip_detection():
    # Observed step-3 directly while on step-1
    verdict = VerdictResult(step_id="step-1", status="done", observed_step_ids=["step-3"], evidence="Jumped ahead", confidence=0.9, source="mock")
    client = ScriptedFakeClient(verdicts=[verdict])
    loop = AgentLoop(client)
    sess = create_test_session()

    update = asyncio.run(loop.process(sess, create_dummy_png()))
    # Both step-1 and step-2 are skipped
    assert sess.engine.states["step-1"] == "skipped"
    assert sess.engine.states["step-2"] == "skipped"
    assert update.action in [Action.WARN, Action.STOP]


# 6. Warning cooldown turns subsequent warning into WAIT
def test_agent_warning_cooldown():
    verdict = VerdictResult(step_id="step-1", status="wrong", observed_step_ids=["step-1"], evidence="Error", warning_text="Err", confidence=0.9, source="mock")
    client = ScriptedFakeClient(verdicts=[verdict, verdict])
    loop = AgentLoop(client)
    sess = create_test_session()

    # First frame -> WARN
    u1 = asyncio.run(loop.process(sess, create_dummy_png(color=(1, 2, 3))))
    assert u1.action == Action.WARN

    # Second frame within 8s -> WAIT (suppressed)
    u2 = asyncio.run(loop.process(sess, create_dummy_png(color=(4, 5, 6))))
    assert u2.action == Action.WAIT
    assert "cooldown" in u2.reason.lower()


# 7. Recheck on low confidence done
def test_agent_recheck():
    # First call low confidence (0.5), second call high confidence (0.88)
    # Must advance once and emit exactly one advance event
    v1 = VerdictResult(step_id="step-1", status="done", observed_step_ids=["step-1"], evidence="Faint", confidence=0.5, source="mock")
    v2 = VerdictResult(step_id="step-1", status="done", observed_step_ids=["step-1"], evidence="Clear", confidence=0.88, source="mock")
    client = ScriptedFakeClient(verdicts=[v1, v2])
    loop = AgentLoop(client)
    sess = create_test_session()

    initial_events_count = len(sess.engine.events)
    update = asyncio.run(loop.process(sess, create_dummy_png()))
    assert client.call_count == 2
    assert update.action == Action.ADVANCE
    # Verify exactly one new event was emitted to the engine
    advance_events = [e for e in sess.engine.events[initial_events_count:] if e.kind == "advance"]
    assert len(advance_events) == 1
    assert sess.engine.states["step-1"] == "done"


def test_agent_recheck_double_low_confidence():
    # First call low confidence (0.5), second call also low confidence (0.55)
    # Must NOT advance
    v1 = VerdictResult(step_id="step-1", status="done", observed_step_ids=["step-1"], evidence="Faint", confidence=0.5, source="mock")
    v2 = VerdictResult(step_id="step-1", status="done", observed_step_ids=["step-1"], evidence="Still faint", confidence=0.55, source="mock")
    client = ScriptedFakeClient(verdicts=[v1, v2])
    loop = AgentLoop(client)
    sess = create_test_session()

    update = asyncio.run(loop.process(sess, create_dummy_png()))
    assert client.call_count == 2
    assert update.action != Action.ADVANCE
    assert sess.engine.states["step-1"] != "done"


# 8. Budget limit reached handling
def test_agent_budget_limit():
    client = ScriptedFakeClient(raise_spend=True)
    loop = AgentLoop(client)
    sess = create_test_session()

    update = asyncio.run(loop.process(sess, create_dummy_png()))
    assert update.action == Action.ASK_USER
    assert "budget" in update.reason.lower()


# 9. Duplicate frame makes no model calls (cached=True)
def test_agent_duplicate_frame_cache():
    verdict = VerdictResult(step_id="step-1", status="in_progress", observed_step_ids=["step-1"], evidence="Working", confidence=0.9, source="mock")
    client = ScriptedFakeClient(verdicts=[verdict])
    loop = AgentLoop(client)
    sess = create_test_session()

    img = create_dummy_png()
    u1 = asyncio.run(loop.process(sess, img))
    assert client.call_count == 1
    assert u1.cached is False

    # Same image again
    u2 = asyncio.run(loop.process(sess, img))
    assert client.call_count == 1  # 0 new calls!
    assert u2.cached is True


# 10. SAM failure is ignored gracefully
def test_agent_sam_failure_ignored():
    verdict = VerdictResult(step_id="step-1", status="done", observed_step_ids=["step-1"], evidence="OK", confidence=0.9, source="mock")
    client = ScriptedFakeClient(verdicts=[verdict], fail_sam=True)
    loop = AgentLoop(client)
    sess = create_test_session()

    update = asyncio.run(loop.process(sess, create_dummy_png()))
    assert update.action == Action.ADVANCE
    assert update.boxes == []


# 11. API frame endpoint gives 415 on invalid image
def test_api_frame_invalid_image():
    client = TestClient(app)
    # Start session first
    proc_resp = client.post("/api/procedure/parse", json={"text": "1. Step one"})
    sess_resp = client.post("/api/session/start", json={"procedure": proc_resp.json()})
    sid = sess_resp.json()["session_id"]

    resp = client.post(f"/api/session/{sid}/frame", content=b"NOT_AN_IMAGE", headers={"Content-Type": "image/png"})
    assert resp.status_code == 415


# 12. API frame endpoint gives 413 on oversize image (>1.5MB)
def test_api_frame_oversize_image():
    client = TestClient(app)
    proc_resp = client.post("/api/procedure/parse", json={"text": "1. Step one"})
    sess_resp = client.post("/api/session/start", json={"procedure": proc_resp.json()})
    sid = sess_resp.json()["session_id"]

    oversize = b"0" * (2 * 1024 * 1024)  # 2 MB
    resp = client.post(f"/api/session/{sid}/frame", content=oversize, headers={"Content-Type": "image/png"})
    assert resp.status_code == 413


# 13. Per-session call limit is enforced per session, not globally across sessions
def test_agent_per_session_call_limit():
    from backend.app.core.config import settings
    verdict = VerdictResult(step_id="step-1", status="in_progress", observed_step_ids=["step-1"], evidence="Typing", confidence=0.9, source="mock")
    client = ScriptedFakeClient(verdicts=[verdict])
    loop = AgentLoop(client)
    sess = create_test_session()
    sess.calls_used = settings.MAX_CALLS_PER_SESSION

    update = asyncio.run(loop.process(sess, create_dummy_png()))
    assert update.action == Action.ASK_USER
    assert "Per-session call limit" in update.reason
    assert client.call_count == 0  # 0 new calls because session already hit cap

