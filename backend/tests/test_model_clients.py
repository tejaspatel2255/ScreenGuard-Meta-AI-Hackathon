import asyncio
import json
import pytest
import httpx
from pathlib import Path
from unittest.mock import AsyncMock, patch

from backend.app.model_clients.base import ProcedureStep
from backend.app.model_clients.mock_client import MockModelClient
from backend.app.model_clients.meta_client import MetaModelClient
from backend.app.model_clients.spend_guard import SpendGuard, SpendLimitReached
from backend.app.model_clients.factory import get_model_client, reset_model_client


def test_mock_client_contracts():
    client = MockModelClient()

    parsed = asyncio.run(client.parse_procedure("Test procedure instruction"))
    assert parsed.source == "mock"
    assert len(parsed.steps) >= 1
    assert parsed.confidence == 1.0

    step = parsed.steps[0]
    verdict = asyncio.run(client.judge_frame(b"dummy_image_data", step, {}))
    assert verdict.source == "mock"
    assert verdict.status in ["done", "in_progress", "wrong", "uncertain"]
    assert 0.0 <= verdict.confidence <= 1.0

    located = asyncio.run(client.locate_elements(b"dummy_image_data", ["Refund button"]))
    assert located.source == "mock"
    assert len(located.elements) == 1
    assert len(located.elements[0].box_2d) == 4

    transcription = asyncio.run(client.transcribe_audio(b"dummy_audio_data"))
    assert transcription.source == "mock"
    assert len(transcription.text) > 0

    export = asyncio.run(client.generate_export(parsed))
    assert export.source == "mock"
    assert "Test procedure instruction" in export.formatted_document
    assert "(Export)" in export.formatted_document


def test_spend_guard_hard_stop():
    guard = SpendGuard(max_spend_usd=0.005)
    guard.record_spend(0.002)
    assert guard.total_estimated_spend_usd == pytest.approx(0.002)

    with pytest.raises(SpendLimitReached):
        guard.record_spend(0.004)


def test_meta_client_success_mocked_http(tmp_path):
    async def _test():
        guard = SpendGuard(max_spend_usd=10.0)
        client = MetaModelClient(api_key="LLM_test_key", spend_guard=guard, cache_dir=tmp_path)

        mock_response = {
            "id": "chatcmpl-123",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": json.dumps({
                            "title": "Refund Flow",
                            "steps": [
                                {
                                    "id": "step-1",
                                    "order": 1,
                                    "instruction": "Click Refund",
                                    "expected_elements": ["Refund"],
                                    "success_condition": "Modal open",
                                    "forbidden_actions": [],
                                    "depends_on": [],
                                    "risk": "low"
                                }
                            ]
                        })
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "prompt_tokens_details": {"cached_tokens": 10}
            }
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = httpx.Response(200, json=mock_response)

            parsed = await client.parse_procedure("Instructions text unique 1")
            assert parsed.title == "Refund Flow"
            assert parsed.source == "real"
            assert len(parsed.steps) == 1
            assert guard.total_estimated_spend_usd > 0.0

            usage = client.usage()
            assert usage["calls_total"] == 1
            assert usage["calls_this_minute"] == 1
            assert usage["estimated_spend_usd"] > 0

    asyncio.run(_test())


def test_meta_client_429_retry_and_backoff(tmp_path):
    async def _test():
        guard = SpendGuard(max_spend_usd=10.0)
        client = MetaModelClient(api_key="LLM_test_key", spend_guard=guard, cache_dir=tmp_path)

        success_data = {
            "choices": [{"message": {"content": json.dumps({"title": "After Retry", "steps": []})}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 10}
        }

        with patch("httpx.AsyncClient.post") as mock_post, patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            resp_429 = httpx.Response(429, headers={"Retry-After": "1"})
            resp_200 = httpx.Response(200, json=success_data)

            mock_post.side_effect = [resp_429, resp_200]

            parsed = await client.parse_procedure("Retry text unique 2")
            assert parsed.title == "After Retry"
            assert mock_post.call_count == 2
            mock_sleep.assert_called_once_with(1.0)

    asyncio.run(_test())


def test_meta_client_timeout_handling(tmp_path):
    async def _test():
        guard = SpendGuard(max_spend_usd=10.0)
        client = MetaModelClient(api_key="LLM_test_key", spend_guard=guard, cache_dir=tmp_path)

        with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Read timed out")), patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(httpx.TimeoutException):
                await client.parse_procedure("Timeout test unique 3")

    asyncio.run(_test())


def test_meta_client_invalid_json_graceful_degrade(tmp_path):
    async def _test():
        guard = SpendGuard(max_spend_usd=10.0)
        client = MetaModelClient(api_key="LLM_test_key", spend_guard=guard, cache_dir=tmp_path)

        bad_resp = {
            "choices": [{"message": {"content": "INVALID_NON_JSON_CONTENT"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 10}
        }

        step = ProcedureStep(
            id="step-1",
            order=1,
            instruction="Do something",
            expected_elements=[],
            success_condition="Done",
        )

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = httpx.Response(200, json=bad_resp)

            verdict = await client.judge_frame(b"img_bytes", step, {})
            assert verdict.status == "uncertain"
            assert verdict.confidence == 0.0
            assert "invalid" in verdict.evidence.lower()

    asyncio.run(_test())


def test_singleton_client_and_reset():
    reset_model_client()
    client1 = get_model_client()
    client2 = get_model_client()
    assert client1 is client2

    reset_model_client()
    client3 = get_model_client()
    assert client3 is not None


def test_mime_type_detection():
    jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"
    png_bytes = b"\x89PNG\r\n\x1a\n"

    assert MetaModelClient._detect_image_mime(jpeg_bytes) == "image/jpeg"
    assert MetaModelClient._detect_image_mime(png_bytes) == "image/png"
