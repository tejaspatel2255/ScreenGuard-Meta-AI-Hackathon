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
        steps: List[ProcedureStep] = [
            ProcedureStep(
                id="step-1",
                order=1,
                instruction="Open the customer refund screen",
                expected_elements=["Refunds Button", "Customer Search Field"],
                success_condition="Refund interface is displayed",
                forbidden_actions=["Click Cancel Transaction"],
                depends_on=[],
                risk="low",
            ),
            ProcedureStep(
                id="step-2",
                order=2,
                instruction="Enter the customer order number and verify details",
                expected_elements=["Order ID Input", "Verify Button"],
                success_condition="Customer order details populated",
                forbidden_actions=["Enter test order ID"],
                depends_on=["step-1"],
                risk="low",
            ),
            ProcedureStep(
                id="step-3",
                order=3,
                instruction="Confirm refund amount and authorize payment",
                expected_elements=["Confirm Refund Button", "Manager Authorization Key"],
                success_condition="Success confirmation modal appears",
                forbidden_actions=["Override safety cap without manager approval"],
                depends_on=["step-2"],
                risk="high",
            ),
        ]
        return ProcedureParseResult(
            title="Mock Customer Refund Procedure",
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
        # Predictable mock verdict: if step is step-3 return high confidence done
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
        # Return mock normalized boxes [ymin, xmin, ymax, xmax]
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
