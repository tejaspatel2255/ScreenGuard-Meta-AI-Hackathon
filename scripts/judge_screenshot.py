import asyncio
import io
import sys
import time
from pathlib import Path

# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.core.config import settings
from backend.app.model_clients.base import ProcedureStep
from backend.app.model_clients.factory import get_model_client


async def judge_screenshot_main():
    if len(sys.argv) < 4:
        print("Usage: python scripts/judge_screenshot.py <screenshot_path> <instruction> <success_condition>")
        print("Example: python scripts/judge_screenshot.py sample_screen.png \"Click the Submit button\" \"A confirmation message is visible\"")
        sys.exit(1)

    image_path = Path(sys.argv[1])
    instruction = sys.argv[2]
    success_condition = sys.argv[3]

    if not image_path.exists():
        print(f"Error: image file '{image_path}' not found.")
        sys.exit(1)

    image_bytes = image_path.read_bytes()

    step = ProcedureStep(
        id="step-verify",
        order=1,
        instruction=instruction,
        expected_elements=[],
        success_condition=success_condition,
        forbidden_actions=[],
        depends_on=[],
        risk="low",
    )

    print("=" * 60)
    print(f"ScreenGuard Judge Screenshot (MODE={settings.MODE}, PROVIDER={settings.PROVIDER})")
    print(f"Image: {image_path} ({len(image_bytes)} bytes)")
    print(f"Instruction: {instruction}")
    print(f"Success Condition: {success_condition}")
    print("=" * 60)

    client = get_model_client()

    t0 = time.time()
    verdict = await client.judge_frame(image_bytes, step, {"completed": []})
    latency = time.time() - t0

    usage = client.usage() if hasattr(client, "usage") else {}

    print(f"Status:        {verdict.status.upper()}")
    print(f"Confidence:    {verdict.confidence:.2f}")
    print(f"Evidence:      {verdict.evidence}")
    print(f"Warning Text:  {verdict.warning_text}")
    print(f"Latency:       {latency:.2f}s")
    print(f"Spend So Far:  ${usage.get('estimated_spend_usd', 0.0):.6f}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(judge_screenshot_main())
