import logging
import re
from typing import List
from backend.app.core.config import settings
from backend.app.model_clients.base import (
    ModelClient,
    ProcedureParseResult,
    ProcedureStep,
)

logger = logging.getLogger("screenguard.procedure_parser")

HIGH_RISK_KEYWORDS = [
    "submit",
    "confirm",
    "approve",
    "refund",
    "delete",
    "pay",
    "send",
    "issue",
]


def parse_deterministic(text: str) -> ProcedureParseResult:
    """Deterministic parser for numbered or bulleted lines.

    - Title from first non-numbered line
    - Quoted words into expected_elements
    - Success condition is a short visual sentence
    - High risk if instruction contains submit, confirm, approve, refund, delete, pay, send, issue
    - Maximum 12 steps
    """
    raw_lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if not raw_lines:
        return ProcedureParseResult(
            title="Empty Procedure",
            steps=[],
            source="mock",
            confidence=1.0,
        )

    title = "Standard Operating Procedure"
    first_line = raw_lines[0]
    # Check if first line is a title (not starting with a list bullet/number)
    if not re.match(r"^(\d+[\.\)]|\-|\*)\s+", first_line):
        title = first_line
        lines_to_process = raw_lines[1:]
    else:
        lines_to_process = raw_lines

    steps: List[ProcedureStep] = []
    order = 1

    for line in lines_to_process:
        if order > 12:
            break

        # Match numbered item or bullet
        cleaned = re.sub(r"^(\d+[\.\)]|\-|\*)\s*", "", line).strip()
        if not cleaned:
            continue

        # Extract quoted words or capitalized terms for expected_elements
        quoted = re.findall(r"['\"]([^'\"]+)['\"]", line)
        if not quoted:
            # Look for capitalized words (e.g. New customer, Name, Submit)
            words = [w.strip(",.()") for w in cleaned.split() if len(w) > 3 and w[0].isupper()]
            quoted = words[:3] if words else ["Action Control"]

        # Risk check
        is_high_risk = any(kw in cleaned.lower() for kw in HIGH_RISK_KEYWORDS)

        # Visual success condition sentence
        success_condition = f"UI displays visible confirmation or state transition for '{cleaned[:50]}'."

        steps.append(
            ProcedureStep(
                id=f"step-{order}",
                order=order,
                instruction=cleaned,
                expected_elements=quoted[:4],
                success_condition=success_condition,
                forbidden_actions=["Do not perform unauthorized steps or premature submissions"],
                depends_on=[f"step-{order-1}"] if order > 1 else [],
                risk="high" if is_high_risk else "low",
            )
        )
        order += 1

    return ProcedureParseResult(
        title=title,
        steps=steps,
        source="mock",
        confidence=1.0,
    )


async def parse_procedure_service(text: str, client: ModelClient) -> ProcedureParseResult:
    """Parses procedure text using the client, falling back to deterministic parser if mock or error."""
    if settings.MODE.lower() == "mock":
        logger.info("MODE=mock: using deterministic procedure parser.")
        return parse_deterministic(text)

    try:
        # Attempt model client parse
        result = await client.parse_procedure(text)
        if result and result.steps and len(result.steps) > 0:
            # Enforce max 12 steps
            result.steps = result.steps[:12]
            return result
    except Exception as e:
        logger.warning("Model client parse_procedure failed: %s. Falling back to deterministic parser.", e)

    # Fallback to deterministic parser
    fallback = parse_deterministic(text)
    fallback.source = "mock"
    return fallback
