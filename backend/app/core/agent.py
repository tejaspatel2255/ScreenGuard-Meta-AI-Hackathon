import asyncio
import hashlib
import io
import logging
import time
import uuid

logger = logging.getLogger("screenguard.agent")
from typing import Any, Dict, List, Optional
from PIL import Image
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.core.policy import Action, AgentPolicy
from backend.app.core.session import Session
from backend.app.core.step_engine import Event, StepStateType
from backend.app.model_clients.base import (
    BoundingBox,
    LocateElementsResult,
    ModelClient,
    ProcedureStep,
    VerdictResult,
)
from backend.app.model_clients.spend_guard import SpendLimitReached


class StepUpdate(BaseModel):
    session_id: str
    frame_id: str
    states: Dict[str, StepStateType]
    current_step_id: Optional[str]
    action: Action
    reason: str
    warning: Optional[str] = None
    blocking: bool = False
    boxes: List[BoundingBox] = Field(default_factory=list)
    verdict: Optional[VerdictResult] = None
    calls_used: int = 0
    estimated_spend_usd: float = 0.0
    latency_ms: float = 0.0
    cached: bool = False
    events: List[Event] = Field(default_factory=list)


class AgentLoop:
    """Core supervisor agent loop: OBSERVE -> VERIFY -> DECIDE -> ACT."""

    def __init__(self, client: ModelClient, cache_enabled: bool = True) -> None:
        self.client = client
        self.cache_enabled = cache_enabled
        self._last_frame_hash: Dict[str, str] = {}  # session_id -> hash
        self._last_step_update: Dict[str, StepUpdate] = {}  # session_id -> StepUpdate

    def _normalize_image(self, image_bytes: bytes) -> bytes:
        """Validates image with Pillow, downscales to max 1024px width, encodes to JPEG quality 80."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise ValueError(f"Invalid image content: {e}")

        # Convert palette/RGBA to RGB
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        max_width = 1024
        if img.width > max_width:
            ratio = max_width / float(img.width)
            new_height = int(float(img.height) * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        out_buf = io.BytesIO()
        img.save(out_buf, format="JPEG", quality=80)
        return out_buf.getvalue()

    async def process(self, session: Session, raw_image_bytes: bytes) -> StepUpdate:
        t0 = time.time()
        frame_id = f"frm-{uuid.uuid4().hex[:8]}"

        # a. SHA-256 deduplication
        hasher = hashlib.sha256()
        hasher.update(raw_image_bytes)
        frame_hash = hasher.hexdigest()

        if self.cache_enabled and self._last_frame_hash.get(session.id) == frame_hash and session.id in self._last_step_update:
            cached_update = self._last_step_update[session.id].model_copy()
            cached_update.cached = True
            cached_update.calls_used = 0
            cached_update.latency_ms = (time.time() - t0) * 1000.0
            return cached_update

        # b. Normalize image
        normalized_bytes = self._normalize_image(raw_image_bytes)

        cur_step = session.engine.current_step
        if not cur_step:
            # Procedure already completed
            return StepUpdate(
                session_id=session.id,
                frame_id=frame_id,
                states=session.engine.states,
                current_step_id=None,
                action=Action.ADVANCE,
                reason="All procedure steps are completed.",
                blocking=False,
                boxes=[],
                verdict=None,
                calls_used=0,
                estimated_spend_usd=self.client.usage().get("estimated_spend_usd", 0.0) if hasattr(self.client, "usage") else 0.0,
                latency_ms=(time.time() - t0) * 1000.0,
                cached=False,
                events=[],
            )

        # Check per-session call limit
        if session.calls_used >= settings.MAX_CALLS_PER_SESSION:
            logger.warning(
                "Per-session call limit (%d) reached for session %s.",
                settings.MAX_CALLS_PER_SESSION,
                session.id,
            )
            return StepUpdate(
                session_id=session.id,
                frame_id=frame_id,
                states=session.engine.states,
                current_step_id=cur_step.id,
                action=Action.ASK_USER,
                reason=f"Per-session call limit ({settings.MAX_CALLS_PER_SESSION}) reached for session '{session.id}'.",
                warning=f"Session call limit ({settings.MAX_CALLS_PER_SESSION}) reached. Please verify remaining steps manually.",
                blocking=False,
                boxes=[],
                verdict=None,
                calls_used=0,
                estimated_spend_usd=self.client.usage().get("estimated_spend_usd", 0.0) if hasattr(self.client, "usage") else 0.0,
                latency_ms=(time.time() - t0) * 1000.0,
                cached=False,
                events=[],
            )

        # Context for judge_frame
        completed_ids = [s.id for s in session.engine.steps if session.engine.states.get(s.id) == "done"]
        all_steps_ctx = [
            {"id": s.id, "order": s.order, "instruction": s.instruction, "success_condition": s.success_condition}
            for s in session.engine.steps
        ]
        recent_decisions = [t["action"] for t in session.trace[-2:]] if session.trace else []

        context = {
            "completed": completed_ids,
            "all_steps": all_steps_ctx,
            "recent_decisions": recent_decisions,
        }

        calls_used = 0
        boxes: List[BoundingBox] = []

        # c. Optional SAM localization
        if settings.USE_SAM and cur_step.expected_elements:
            try:
                sam_res = await self.client.locate_elements(normalized_bytes, cur_step.expected_elements)
                boxes = sam_res.elements
                calls_used += 1
            except Exception:
                boxes = []

        # d. Muse Spark / Vision judgment with SpendGuard handling
        verdict: Optional[VerdictResult] = None
        try:
            verdict = await self.client.judge_frame(normalized_bytes, cur_step, context)
            calls_used += 1
        except SpendLimitReached:
            update = StepUpdate(
                session_id=session.id,
                frame_id=frame_id,
                states=session.engine.states,
                current_step_id=cur_step.id,
                action=Action.ASK_USER,
                reason="Budget limit reached. Cannot make more model calls without user approval.",
                warning=f"Estimated budget limit reached (${settings.MAX_ESTIMATED_SPEND_USD:.2f} max spend).",
                blocking=True,
                boxes=boxes,
                verdict=None,
                calls_used=calls_used,
                estimated_spend_usd=self.client.usage().get("estimated_spend_usd", 0.0) if hasattr(self.client, "usage") else 0.0,
                latency_ms=(time.time() - t0) * 1000.0,
                cached=False,
                events=[],
            )
            return update
        except Exception as e:
            # Graceful degrade on model error
            verdict = VerdictResult(
                step_id=cur_step.id,
                status="uncertain",
                observed_step_ids=[],
                evidence=f"Model verification error: {e}",
                confidence=0.0,
                source="real",
            )

        # e. Handle optional RECHECK before mutating StepEngine state
        threshold = settings.CONFIDENCE_HIGH_RISK if cur_step.risk == "high" else settings.CONFIDENCE_ADVANCE
        needs_recheck = False
        if verdict.status == "done" and verdict.confidence < threshold:
            needs_recheck = True
        elif verdict.status == "uncertain" and cur_step.risk == "high":
            needs_recheck = True

        is_recheck = False
        if needs_recheck and calls_used < 3 and session.calls_used + calls_used < settings.MAX_CALLS_PER_SESSION:
            try:
                second_verdict = await self.client.judge_frame(normalized_bytes, cur_step, context)
                calls_used += 1
                if second_verdict.confidence > verdict.confidence:
                    verdict = second_verdict
                is_recheck = True
            except Exception:
                is_recheck = True

        # Apply chosen verdict to StepEngine and Policy EXACTLY ONCE
        engine_events = session.engine.apply_verdict(verdict)
        decision = AgentPolicy.decide(verdict, cur_step, engine_events, session.engine, is_recheck=is_recheck)

        session.calls_used += calls_used

        latency_ms = (time.time() - t0) * 1000.0
        spend_now = self.client.usage().get("estimated_spend_usd", 0.0) if hasattr(self.client, "usage") else 0.0

        # Trace entry
        trace_entry = {
            "id": f"trc-{uuid.uuid4().hex[:8]}",
            "ts": time.time(),
            "action": decision.action.value,
            "reason": decision.reason,
            "step_id": cur_step.id,
            "status": verdict.status,
            "confidence": verdict.confidence,
            "evidence": verdict.evidence,
            "warning": decision.warning_text,
            "calls_used": calls_used,
            "latency_ms": latency_ms,
        }
        session.trace.append(trace_entry)

        step_update = StepUpdate(
            session_id=session.id,
            frame_id=frame_id,
            states=session.engine.states,
            current_step_id=session.engine.current_step_id,
            action=decision.action,
            reason=decision.reason,
            warning=decision.warning_text,
            blocking=(decision.action == Action.STOP),
            boxes=boxes,
            verdict=verdict,
            calls_used=calls_used,
            estimated_spend_usd=spend_now,
            latency_ms=latency_ms,
            cached=False,
            events=engine_events,
        )

        self._last_frame_hash[session.id] = frame_hash
        self._last_step_update[session.id] = step_update
        return step_update
