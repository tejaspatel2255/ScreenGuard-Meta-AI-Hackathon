import time
from typing import Any, Callable, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.model_clients.base import ProcedureStep, VerdictResult

StepStateType = Literal["pending", "active", "done", "wrong", "skipped", "uncertain"]


class Event(BaseModel):
    ts: float
    step_id: str
    kind: str  # advance, skip, wrong, uncertain, in_progress, override, restart
    reason: str


class StepEngine:
    """Pure Python, no I/O, step engine state machine with injectable clock."""

    def __init__(
        self,
        steps: List[ProcedureStep],
        clock: Optional[Callable[[], float]] = None,
        confidence_advance: Optional[float] = None,
        confidence_high_risk: Optional[float] = None,
        warning_cooldown_seconds: Optional[float] = None,
    ) -> None:
        self.steps = sorted(steps, key=lambda s: s.order)
        self.clock = clock or time.time
        self.confidence_advance = confidence_advance or settings.CONFIDENCE_ADVANCE
        self.confidence_high_risk = confidence_high_risk or settings.CONFIDENCE_HIGH_RISK
        self.warning_cooldown_seconds = warning_cooldown_seconds or settings.WARNING_COOLDOWN_SECONDS

        self.step_map: Dict[str, ProcedureStep] = {s.id: s for s in self.steps}
        self.states: Dict[str, StepStateType] = {}
        self.last_warnings: Dict[str, float] = {}  # key: f"{step_id}:{kind}" -> ts
        self.events: List[Event] = []

        self._init_states()

    def _init_states(self) -> None:
        """Initializes all steps: first step active, rest pending."""
        for i, step in enumerate(self.steps):
            self.states[step.id] = "active" if i == 0 else "pending"

    @property
    def current_step(self) -> Optional[ProcedureStep]:
        """Returns the first step that is not done or skipped."""
        for step in self.steps:
            state = self.states.get(step.id)
            if state not in ("done", "skipped"):
                return step
        return None

    @property
    def current_step_id(self) -> Optional[str]:
        cur = self.current_step
        return cur.id if cur else None

    @property
    def progress(self) -> Dict[str, int]:
        done_count = sum(1 for s in self.steps if self.states.get(s.id) == "done")
        return {"done": done_count, "total": len(self.steps)}

    @property
    def is_complete(self) -> bool:
        return self.current_step is None

    def can_warn(self, step_id: str, kind: str) -> bool:
        """Returns False if the same warning was issued within WARNING_COOLDOWN_SECONDS."""
        now = self.clock()
        key = f"{step_id}:{kind}"
        last_ts = self.last_warnings.get(key)
        if last_ts is not None and (now - last_ts) < self.warning_cooldown_seconds:
            return False
        return True

    def record_warning(self, step_id: str, kind: str) -> None:
        key = f"{step_id}:{kind}"
        self.last_warnings[key] = self.clock()

    def apply_verdict(self, verdict: VerdictResult) -> List[Event]:
        """Updates engine state based on model verdict and returns produced events."""
        now = self.clock()
        new_events: List[Event] = []
        cur = self.current_step

        if not cur:
            return new_events

        # 1. Skip detection: if observed_step_ids contains a step with higher order than current
        observed_steps = [self.step_map[sid] for sid in verdict.observed_step_ids if sid in self.step_map]
        higher_observed = [s for s in observed_steps if s.order > cur.order]

        if higher_observed:
            # Mark every earlier not-done step as skipped
            highest_order = max(s.order for s in higher_observed)
            for s in self.steps:
                if s.order < highest_order and self.states.get(s.id) not in ("done", "skipped"):
                    self.states[s.id] = "skipped"
                    evt = Event(
                        ts=now,
                        step_id=s.id,
                        kind="skip",
                        reason=f"Step skipped because evidence appeared for later step order {highest_order}",
                    )
                    new_events.append(evt)
                    self.events.append(evt)

            # Re-evaluate current step after skipping
            cur = self.current_step
            if not cur:
                return new_events

        # 2. Check current step verdict status
        required_conf = self.confidence_high_risk if cur.risk == "high" else self.confidence_advance

        if verdict.status == "done" and verdict.confidence >= required_conf:
            self.states[cur.id] = "done"
            evt = Event(
                ts=now,
                step_id=cur.id,
                kind="advance",
                reason=f"Completed with confidence {verdict.confidence:.2f} >= {required_conf:.2f}. {verdict.evidence}",
            )
            new_events.append(evt)
            self.events.append(evt)

            # Activate next pending step if available
            next_step = self.current_step
            if next_step and self.states.get(next_step.id) == "pending":
                self.states[next_step.id] = "active"

        elif verdict.status == "in_progress":
            self.states[cur.id] = "active"
            evt = Event(
                ts=now,
                step_id=cur.id,
                kind="in_progress",
                reason=f"Step in progress. {verdict.evidence}",
            )
            new_events.append(evt)
            self.events.append(evt)

        elif verdict.status == "wrong":
            self.states[cur.id] = "wrong"
            warn_allowed = self.can_warn(cur.id, "wrong")
            if warn_allowed:
                self.record_warning(cur.id, "wrong")
            evt = Event(
                ts=now,
                step_id=cur.id,
                kind="wrong",
                reason=verdict.warning_text or verdict.evidence or "Incorrect action or violation detected",
            )
            new_events.append(evt)
            self.events.append(evt)

        elif verdict.status == "uncertain" or (verdict.status == "done" and verdict.confidence < required_conf):
            # No state change for current step, record an uncertain event
            reason = (
                f"Confidence {verdict.confidence:.2f} below threshold {required_conf:.2f}"
                if verdict.status == "done"
                else verdict.evidence or "Visual evidence uncertain"
            )
            evt = Event(
                ts=now,
                step_id=cur.id,
                kind="uncertain",
                reason=reason,
            )
            new_events.append(evt)
            self.events.append(evt)

        return new_events

    def override(self, step_id: str, state: StepStateType) -> Event:
        """Manual override for a step state."""
        if step_id not in self.step_map:
            raise KeyError(f"Step '{step_id}' not found")

        self.states[step_id] = state
        now = self.clock()
        evt = Event(
            ts=now,
            step_id=step_id,
            kind="override",
            reason=f"Manually overridden to {state}",
        )
        self.events.append(evt)

        # Ensure next step becomes active if previous completed
        cur = self.current_step
        if cur and self.states.get(cur.id) == "pending":
            self.states[cur.id] = "active"

        return evt

    def restart(self) -> Event:
        """Restarts the procedure."""
        self._init_states()
        self.last_warnings.clear()
        now = self.clock()
        evt = Event(
            ts=now,
            step_id=self.steps[0].id if self.steps else "",
            kind="restart",
            reason="Procedure restarted",
        )
        self.events.append(evt)
        return evt
