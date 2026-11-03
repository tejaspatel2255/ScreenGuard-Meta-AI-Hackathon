import asyncio
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.core.procedure_parser import parse_deterministic, parse_procedure_service
from backend.app.core.step_engine import StepEngine
from backend.app.main import app
from backend.app.model_clients.base import ProcedureStep, VerdictResult
from backend.app.model_clients.mock_client import MockModelClient


def create_sample_steps():
    return [
        ProcedureStep(
            id="step-1",
            order=1,
            instruction="Sign in to the application",
            expected_elements=["Sign In"],
            success_condition="Dashboard is displayed",
            forbidden_actions=[],
            risk="low",
        ),
        ProcedureStep(
            id="step-2",
            order=2,
            instruction="Click New customer and fill name",
            expected_elements=["Name Input"],
            success_condition="Name field populated",
            forbidden_actions=[],
            risk="low",
        ),
        ProcedureStep(
            id="step-3",
            order=3,
            instruction="Submit and approve application",
            expected_elements=["Submit"],
            success_condition="Confirmation screen displayed",
            forbidden_actions=["Cancel Transaction"],
            risk="high",
        ),
    ]


# 1. Step Engine: Advance on normal done
def test_engine_advance_low_risk():
    steps = create_sample_steps()
    engine = StepEngine(steps, confidence_advance=0.7)
    assert engine.current_step_id == "step-1"
    assert engine.states["step-1"] == "active"
    assert engine.states["step-2"] == "pending"

    verdict = VerdictResult(
        step_id="step-1",
        status="done",
        observed_step_ids=["step-1"],
        evidence="Dashboard visible",
        confidence=0.8,
        source="mock",
    )
    events = engine.apply_verdict(verdict)
    assert len(events) == 1
    assert events[0].kind == "advance"
    assert engine.states["step-1"] == "done"
    assert engine.states["step-2"] == "active"
    assert engine.current_step_id == "step-2"


# 2. Step Engine: Low confidence does not advance
def test_engine_low_confidence_no_advance():
    steps = create_sample_steps()
    engine = StepEngine(steps, confidence_advance=0.7)

    verdict = VerdictResult(
        step_id="step-1",
        status="done",
        observed_step_ids=["step-1"],
        evidence="Vague screen",
        confidence=0.5,
        source="mock",
    )
    events = engine.apply_verdict(verdict)
    assert len(events) == 1
    assert events[0].kind == "uncertain"
    assert engine.states["step-1"] == "active"
    assert engine.current_step_id == "step-1"


# 3. Step Engine: High risk requires higher confidence (0.85)
def test_engine_high_risk_confidence_threshold():
    steps = create_sample_steps()
    engine = StepEngine(steps, confidence_advance=0.7, confidence_high_risk=0.85)

    # Force to step-3 (high risk)
    engine.override("step-1", "done")
    engine.override("step-2", "done")
    assert engine.current_step_id == "step-3"
    assert engine.current_step.risk == "high"

    # Confidence 0.80 is >= 0.70 but < 0.85 (must not advance)
    verdict = VerdictResult(
        step_id="step-3",
        status="done",
        observed_step_ids=["step-3"],
        evidence="Partial confirmation",
        confidence=0.80,
        source="mock",
    )
    events = engine.apply_verdict(verdict)
    assert events[0].kind == "uncertain"
    assert engine.states["step-3"] == "active"

    # Confidence 0.90 is >= 0.85 (advances)
    verdict_high = VerdictResult(
        step_id="step-3",
        status="done",
        observed_step_ids=["step-3"],
        evidence="Full confirmation modal",
        confidence=0.90,
        source="mock",
    )
    events2 = engine.apply_verdict(verdict_high)
    assert events2[0].kind == "advance"
    assert engine.states["step-3"] == "done"
    assert engine.is_complete is True


# 4. Step Engine: Out of order evidence triggers skip
def test_engine_out_of_order_skip_detection():
    steps = create_sample_steps()
    engine = StepEngine(steps)
    assert engine.current_step_id == "step-1"

    # Evidence for step-3 appears while step-1 is still active
    verdict = VerdictResult(
        step_id="step-1",
        status="done",
        observed_step_ids=["step-3"],
        evidence="User jumped directly to final submit screen",
        confidence=0.95,
        source="mock",
    )
    events = engine.apply_verdict(verdict)
    # Both step-1 and step-2 should be skipped
    skip_events = [e for e in events if e.kind == "skip"]
    assert len(skip_events) == 2
    assert engine.states["step-1"] == "skipped"
    assert engine.states["step-2"] == "skipped"


# 5. Step Engine: In-progress verdict keeps step active
def test_engine_in_progress_verdict():
    steps = create_sample_steps()
    engine = StepEngine(steps)

    verdict = VerdictResult(
        step_id="step-1",
        status="in_progress",
        observed_step_ids=["step-1"],
        evidence="User typing login credentials",
        confidence=0.9,
        source="mock",
    )
    events = engine.apply_verdict(verdict)
    assert len(events) == 1
    assert events[0].kind == "in_progress"
    assert engine.states["step-1"] == "active"


# 6. Step Engine: Wrong status marks step wrong
def test_engine_wrong_status():
    steps = create_sample_steps()
    engine = StepEngine(steps)

    verdict = VerdictResult(
        step_id="step-1",
        status="wrong",
        observed_step_ids=["step-1"],
        evidence="User clicked Cancel Transaction instead of Sign In",
        warning_text="Do not click cancel!",
        confidence=0.95,
        source="mock",
    )
    events = engine.apply_verdict(verdict)
    assert len(events) == 1
    assert events[0].kind == "wrong"
    assert engine.states["step-1"] == "wrong"


# 7. Step Engine: Warning cooldown (8 seconds)
def test_engine_warning_cooldown():
    current_time = 100.0

    def mock_clock():
        return current_time

    steps = create_sample_steps()
    engine = StepEngine(steps, clock=mock_clock, warning_cooldown_seconds=8.0)

    # First warning allowed
    assert engine.can_warn("step-1", "wrong") is True
    engine.record_warning("step-1", "wrong")

    # Within 8 seconds -> disallowed
    current_time = 104.0
    assert engine.can_warn("step-1", "wrong") is False

    # After 8 seconds -> allowed
    current_time = 108.5
    assert engine.can_warn("step-1", "wrong") is True


# 8. Step Engine: Manual override
def test_engine_manual_override():
    steps = create_sample_steps()
    engine = StepEngine(steps)

    evt = engine.override("step-1", "done")
    assert evt.kind == "override"
    assert engine.states["step-1"] == "done"
    assert engine.states["step-2"] == "active"
    assert engine.current_step_id == "step-2"


# 9. Step Engine: Restart
def test_engine_restart():
    steps = create_sample_steps()
    engine = StepEngine(steps)
    engine.override("step-1", "done")
    engine.override("step-2", "done")
    assert engine.progress["done"] == 2

    restart_evt = engine.restart()
    assert restart_evt.kind == "restart"
    assert engine.progress["done"] == 0
    assert engine.states["step-1"] == "active"
    assert engine.states["step-2"] == "pending"


# 10. Step Engine: Progress and Completion tracking
def test_engine_progress_and_completion():
    steps = create_sample_steps()
    engine = StepEngine(steps)
    assert engine.progress == {"done": 0, "total": 3}
    assert engine.is_complete is False

    engine.override("step-1", "done")
    engine.override("step-2", "skipped")
    engine.override("step-3", "done")

    assert engine.progress == {"done": 2, "total": 3}
    assert engine.is_complete is True
    assert engine.current_step is None


# 11. Deterministic Parser on sample_procedure.txt
def test_deterministic_parser_sample_procedure():
    sample_path = Path(__file__).resolve().parent.parent.parent / "docs" / "sample_procedure.txt"
    assert sample_path.exists()
    text = sample_path.read_text(encoding="utf-8")

    parsed = parse_deterministic(text)
    assert "Acme Admin" in parsed.title
    assert len(parsed.steps) == 10  # Sample procedure has 10 steps
    assert parsed.steps[0].order == 1
    assert parsed.steps[9].order == 10
    # Step 9 is "Click Submit" -> should have risk="high"
    assert parsed.steps[8].risk == "high"


# 12. Parser Service fallback in mock mode
def test_parse_procedure_service_mock_mode():
    client = MockModelClient()
    parsed = asyncio.run(parse_procedure_service("1. First step\n2. Second step", client))
    assert len(parsed.steps) == 2
    assert parsed.source == "mock"


# 13. API: POST /api/procedure/parse
def test_api_parse_procedure():
    with patch("backend.app.core.config.settings.MODE", "mock"):
        client = TestClient(app)
        resp = client.post("/api/procedure/parse", json={"text": "1. Do step one\n2. Submit data"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["steps"]) == 2
        assert data["steps"][1]["risk"] == "high"


# 14. API: Session lifecycle (start, get, override, restart)
def test_api_session_lifecycle():
    with patch("backend.app.core.config.settings.MODE", "mock"):
        client = TestClient(app)

        # 1. Start session
        parse_resp = client.post("/api/procedure/parse", json={"text": "1. Login\n2. Confirm"})
        proc = parse_resp.json()

        start_resp = client.post("/api/session/start", json={"procedure": proc})
        assert start_resp.status_code == 200
        start_data = start_resp.json()
        sess_id = start_data["session_id"]
        assert start_data["current_step_id"] == "step-1"
        assert start_data["states"]["step-1"] == "active"

        # 2. Get session
        get_resp = client.get(f"/api/session/{sess_id}")
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["progress"] == {"done": 0, "total": 2}

        # 3. Override step
        override_resp = client.post(f"/api/session/{sess_id}/override", json={"step_id": "step-1", "state": "done"})
        assert override_resp.status_code == 200
        ov_data = override_resp.json()
        assert ov_data["states"]["step-1"] == "done"
        assert ov_data["current_step_id"] == "step-2"

        # 4. Restart session
        restart_resp = client.post(f"/api/session/{sess_id}/restart")
        assert restart_resp.status_code == 200
        rst_data = restart_resp.json()
        assert rst_data["states"]["step-1"] == "active"
        assert rst_data["progress"]["done"] == 0


# 15. API: Budget endpoint
def test_api_budget_endpoint():
    client = TestClient(app)
    resp = client.get("/api/budget")
    assert resp.status_code == 200
    data = resp.json()
    assert "calls_total" in data
    assert "estimated_spend_usd" in data
    assert "spend_limit_usd" in data
