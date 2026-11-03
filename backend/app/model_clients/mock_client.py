import re
from typing import Any, Dict, List
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


class MockModelClient(ModelClient):
    """Deterministic fake responses for offline development and testing.

    Every result carries source='mock'.
    """

    def __init__(self) -> None:
        pass

    async def parse_procedure(self, text: str) -> ProcedureParseResult:
        """Parses procedure text deterministically instead of ignoring it."""
        lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
        steps: List[ProcedureStep] = []
        order = 1

        for line in lines:
            # Check for numbered list items like "1. Do something" or "- Do something"
            cleaned = re.sub(r"^(\d+[\.\)]|\-|\*)\s*", "", line)
            if not cleaned:
                continue

            # Infer risk and elements simply
            is_high_risk = any(kw in cleaned.lower() for kw in ["confirm", "authorize", "submit", "delete", "override", "manager"])
            
            # Simple keyword extraction for expected elements
            words = [w.strip(",.()") for w in cleaned.split() if len(w) > 3 and w[0].isupper()]
            expected = words[:3] if words else ["Action Button"]

            steps.append(
                ProcedureStep(
                    id=f"step-{order}",
                    order=order,
                    instruction=cleaned,
                    expected_elements=expected,
                    success_condition=f"Visible UI state confirming completion of: {cleaned}",
                    forbidden_actions=["Do not perform unauthorized steps"],
                    depends_on=[f"step-{order-1}"] if order > 1 else [],
                    risk="high" if is_high_risk else "low",
                )
            )
            order += 1

        if not steps:
            steps.append(
                ProcedureStep(
                    id="step-1",
                    order=1,
                    instruction="Open procedure screen",
                    expected_elements=["Screen"],
                    success_condition="Screen loaded",
                    risk="low",
                )
            )

        title = "Parsed Procedure"
        if lines:
            first_line = lines[0]
            if not re.match(r"^(\d+[\.\)]|\-|\*)", first_line):
                title = first_line

        return ProcedureParseResult(
            title=title,
            steps=steps,
            source="mock",
            confidence=1.0,
        )

    async def judge_frame(
        self,
        image_bytes: bytes,
        step: ProcedureStep,
        context: Dict[str, Any],
    ) -> VerdictResult:
        return VerdictResult(
            step_id=step.id,
            status="done",
            observed_step_ids=[step.id],
            evidence=f"Mock evaluation observed UI fulfilling '{step.instruction}'.",
            warning_text=None,
            confidence=0.95,
            source="mock",
        )

    async def locate_elements(
        self,
        image_bytes: bytes,
        prompts: List[str],
    ) -> LocateElementsResult:
        elements: List[BoundingBox] = []
        for i, prompt in enumerate(prompts):
            offset = i * 0.1
            elements.append(
                BoundingBox(
                    label=prompt,
                    box_2d=[0.1 + offset, 0.1 + offset, 0.2 + offset, 0.4 + offset],
                    confidence=0.92,
                )
            )
        return LocateElementsResult(elements=elements, source="mock")

    async def transcribe_audio(self, audio_bytes: bytes) -> TranscriptionResult:
        return TranscriptionResult(
            text="First open the customer refund tab. Then enter order number 12345. Finally confirm the refund.",
            language="en",
            duration_seconds=5.0,
            source="mock",
        )

    async def generate_export(self, procedure: ProcedureParseResult) -> ExportResult:
        lines = [f"# {procedure.title} (Export)", ""]
        for s in procedure.steps:
            lines.append(f"{s.order}. **{s.instruction}** (Risk: {s.risk})")
            lines.append(f"   Success: {s.success_condition}")
        return ExportResult(
            formatted_document="\n".join(lines),
            format_type="markdown",
            source="mock",
        )
