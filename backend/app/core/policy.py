from enum import Enum
from typing import List, Literal, NamedTuple, Optional
from backend.app.core.config import settings
from backend.app.core.step_engine import Event, StepEngine
from backend.app.model_clients.base import ProcedureStep, VerdictResult


class Action(str, Enum):
    ADVANCE = "ADVANCE"
    WAIT = "WAIT"
    WARN = "WARN"
    RECHECK = "RECHECK"
    ASK_USER = "ASK_USER"
    STOP = "STOP"


class PolicyDecision(NamedTuple):
    action: Action
    reason: str
    warning_text: Optional[str] = None


class AgentPolicy:
    """Decides supervisor action based on model verdict, current step risk, and engine state."""

    @staticmethod
    def decide(
        verdict: VerdictResult,
        step: ProcedureStep,
        engine_events: List[Event],
        engine: StepEngine,
        is_recheck: bool = False,
    ) -> PolicyDecision:
        threshold = settings.CONFIDENCE_HIGH_RISK if step.risk == "high" else settings.CONFIDENCE_ADVANCE

        # 1. Check if a skip was detected by the engine
        skip_events = [e for e in engine_events if e.kind == "skip"]
        if skip_events:
            # Check if any skipped step was high-risk
            skipped_steps = [engine.step_map.get(e.step_id) for e in skip_events if e.step_id in engine.step_map]
            has_high_risk_skip = any(s.risk == "high" for s in skipped_steps if s)

            warning = f"Step was skipped: {skip_events[0].reason}"
            if has_high_risk_skip:
                return PolicyDecision(Action.STOP, f"Critical high-risk step was skipped: {skip_events[0].step_id}", warning)

            if not engine.can_warn(step.id, "skip"):
                return PolicyDecision(Action.WAIT, "Warning suppressed by cooldown", None)

            engine.record_warning(step.id, "skip")
            return PolicyDecision(Action.WARN, f"Out-of-order action detected: {skip_events[0].reason}", warning)

        # 2. Status: done
        if verdict.status == "done":
            if verdict.confidence >= threshold:
                return PolicyDecision(
                    Action.ADVANCE,
                    f"Step '{step.instruction}' confirmed with confidence {verdict.confidence:.2f} >= {threshold:.2f}",
                    None,
                )
            # Low confidence done -> RECHECK if not already rechecked
            if not is_recheck:
                return PolicyDecision(
                    Action.RECHECK,
                    f"Completion observed but confidence {verdict.confidence:.2f} < {threshold:.2f}. Requesting recheck.",
                    None,
                )
            # After recheck still below threshold -> WAIT
            return PolicyDecision(
                Action.WAIT,
                f"Confidence {verdict.confidence:.2f} remains below threshold after recheck.",
                None,
            )

        # 3. Status: in_progress
        if verdict.status == "in_progress":
            return PolicyDecision(Action.WAIT, "User is actively working on the step.", None)

        # 4. Status: wrong
        if verdict.status == "wrong":
            warn_msg = verdict.warning_text or "Incorrect action or input observed."
            if step.risk == "high":
                if verdict.confidence >= 0.8:
                    return PolicyDecision(
                        Action.STOP,
                        f"High-risk violation detected on step '{step.instruction}': {verdict.evidence}",
                        warn_msg,
                    )
                elif not is_recheck:
                    return PolicyDecision(
                        Action.RECHECK,
                        f"Potential high-risk violation with confidence {verdict.confidence:.2f} < 0.80. Requesting recheck.",
                        None,
                    )
                else:
                    return PolicyDecision(
                        Action.STOP,
                        f"High-risk violation confirmed on recheck: {verdict.evidence}",
                        warn_msg,
                    )

            # Low-risk step debouncing: requires 2 consecutive wrong verdicts before warning
            consecutive = engine.consecutive_wrong.get(step.id, 1)
            if consecutive < 2:
                return PolicyDecision(
                    Action.WAIT,
                    f"Initial deviation observed on step '{step.instruction}'. Debouncing pending second frame confirmation.",
                    None,
                )

            if not engine.can_warn(step.id, "wrong"):
                return PolicyDecision(Action.WAIT, "Warning suppressed by cooldown", None)

            engine.record_warning(step.id, "wrong")
            return PolicyDecision(
                Action.WARN,
                f"Violation detected on step '{step.instruction}': {verdict.evidence}",
                warn_msg,
            )

        # 5. Status: uncertain
        if is_recheck and step.risk == "high" and verdict.confidence < 0.5:
            return PolicyDecision(
                Action.ASK_USER,
                f"Unable to verify high-risk step '{step.instruction}'. User confirmation needed.",
                "Visual evidence unclear on high-risk step. Please confirm completion.",
            )

        return PolicyDecision(Action.WAIT, "Visual evidence inconclusive; waiting for clearer screen update.", None)
