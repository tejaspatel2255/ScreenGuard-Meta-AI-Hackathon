import asyncio
import io
import json
import os
import sys
import time
from pathlib import Path
from PIL import Image

# Ensure backend can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.core.config import settings
from backend.app.model_clients import (
    ModelClient,
    ProcedureStep,
    SpendGuard,
    get_model_client,
)


def create_dummy_png() -> bytes:
    img = Image.new("RGB", (200, 100), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_dummy_wav() -> bytes:
    # 1 second of silence in WAV
    import wave
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x00" * 32000)
    return buf.getvalue()


async def run_smoke_test():
    print("=" * 60)
    print(f"ScreenGuard Smoke Test (MODE={settings.MODE}, PROVIDER={settings.PROVIDER})")
    print("=" * 60)

    client: ModelClient = get_model_client()
    output_dir = Path(__file__).resolve().parent.parent / "docs" / "sample_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    dummy_image = create_dummy_png()
    dummy_audio = create_dummy_wav()

    # 1. Text: Parse procedure
    print("\n[1/4] Testing parse_procedure (Muse Spark)...")
    t0 = time.time()
    sample_text = (
        "1. Click the New Refund button.\n"
        "2. Enter customer transaction ID and verify details.\n"
        "3. Click Issue Refund."
    )
    parsed = await client.parse_procedure(sample_text)
    latency_parse = time.time() - t0
    print(f"Status: OK | Latency: {latency_parse:.2f}s | Source: {parsed.source} | Steps: {len(parsed.steps)}")
    (output_dir / "parse_procedure_sample.json").write_text(parsed.model_dump_json(indent=2), encoding="utf-8")

    # 2. Vision: Judge frame
    print("\n[2/4] Testing judge_frame (Muse Spark)...")
    t0 = time.time()
    step = parsed.steps[0] if parsed.steps else ProcedureStep(
        id="step-1",
        order=1,
        instruction="Click the New Refund button",
        expected_elements=["New Refund"],
        success_condition="Refund form opens",
    )
    verdict = await client.judge_frame(dummy_image, step, {"completed": []})
    latency_judge = time.time() - t0
    print(f"Status: OK | Latency: {latency_judge:.2f}s | Source: {verdict.source} | Verdict: {verdict.status} (conf: {verdict.confidence})")
    (output_dir / "judge_frame_sample.json").write_text(verdict.model_dump_json(indent=2), encoding="utf-8")

    # 3. Vision Segmentation: Locate elements (SAM 3.1)
    if settings.USE_SAM:
        print("\n[3/4] Testing locate_elements (SAM 3.1)...")
        t0 = time.time()
        located = await client.locate_elements(dummy_image, ["New Refund button", "Order ID field"])
        latency_sam = time.time() - t0
        print(f"Status: OK | Latency: {latency_sam:.2f}s | Source: {located.source} | Found boxes: {len(located.elements)}")
        (output_dir / "locate_elements_sample.json").write_text(located.model_dump_json(indent=2), encoding="utf-8")
    else:
        print("\n[3/4] SAM 3.1 skipped (USE_SAM=false)")

    # 4. Audio: Transcribe audio (Muse Voice Transcribe)
    if settings.USE_VOICE:
        print("\n[4/4] Testing transcribe_audio (Muse Voice Transcribe)...")
        t0 = time.time()
        transcribed = await client.transcribe_audio(dummy_audio)
        latency_voice = time.time() - t0
        print(f"Status: OK | Latency: {latency_voice:.2f}s | Source: {transcribed.source} | Text: '{transcribed.text}'")
        (output_dir / "transcribe_audio_sample.json").write_text(transcribed.model_dump_json(indent=2), encoding="utf-8")
    else:
        print("\n[4/4] Muse Voice Transcribe skipped (USE_VOICE=false)")

    print("\n" + "=" * 60)
    print("Smoke test completed successfully!")
    print(f"Sample outputs saved to: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_smoke_test())
