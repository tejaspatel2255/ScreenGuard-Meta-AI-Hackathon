import asyncio
import base64
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

from backend.app.core.config import settings
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
from backend.app.model_clients.spend_guard import SpendGuard, SpendLimitReached

logger = logging.getLogger("screenguard.meta_client")

# Task 1d: Named constants for models and endpoints
SPARK_MODEL = "muse-spark-1.3"
SAM_MODEL = "sam-3.1"
VOICE_MODEL = "muse-voice-transcribe-1.0"
CHAT_PATH = "/chat/completions"
SEGMENT_PATH = "/segmentation"
VOICE_PATH = "/audio/transcriptions"


class MetaModelClient(ModelClient):
    """Real client for Meta Model API adhering to docs/meta_api_notes.md and PROJECT_RULES.md."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        spend_guard: Optional[SpendGuard] = None,
        cache_dir: Optional[Path] = None,
    ) -> None:
        self.api_key = api_key or settings.META_API_KEY
        self.base_url = (base_url or settings.META_API_BASE_URL or "https://api.meta.ai/v1").rstrip("/")
        self.spend_guard = spend_guard or SpendGuard(
            max_spend_usd=settings.MAX_ESTIMATED_SPEND_USD
        )
        self.cache_dir = cache_dir or (Path(__file__).resolve().parent.parent.parent.parent / "cache" / "model_responses")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.call_count_session = 0
        self.calls_in_current_minute: List[float] = []

        # Load prompts
        prompts_dir = Path(__file__).resolve().parent.parent / "prompts"
        parse_p_path = prompts_dir / "parse_procedure.txt"
        judge_p_path = prompts_dir / "judge_frame.txt"
        self.prompt_parse = parse_p_path.read_text(encoding="utf-8") if parse_p_path.exists() else ""
        self.prompt_judge = judge_p_path.read_text(encoding="utf-8") if judge_p_path.exists() else ""

    async def _enforce_limits(self) -> None:
        """Enforces MAX_CALLS_PER_SESSION and MAX_CALLS_PER_MINUTE asynchronously with 10s timeout."""
        if self.call_count_session >= settings.MAX_CALLS_PER_SESSION:
            raise RuntimeError(
                f"MAX_CALLS_PER_SESSION ({settings.MAX_CALLS_PER_SESSION}) reached. Refusing calls."
            )

        start_wait = time.time()
        while True:
            now = time.time()
            self.calls_in_current_minute = [t for t in self.calls_in_current_minute if now - t < 60.0]
            if len(self.calls_in_current_minute) < settings.MAX_CALLS_PER_MINUTE:
                break

            waited = now - start_wait
            if waited >= 10.0:
                raise TimeoutError(
                    f"Exceeded 10s wait limit waiting for per-minute rate limit ({settings.MAX_CALLS_PER_MINUTE} rpm)."
                )

            sleep_duration = min(60.0 - (now - self.calls_in_current_minute[0]) + 0.1, 10.0 - waited)
            logger.warning(
                "Per-minute call limit (%d) reached. Asynchronously waiting for %.2fs",
                settings.MAX_CALLS_PER_MINUTE,
                sleep_duration,
            )
            await asyncio.sleep(max(0.1, min(sleep_duration, 2.0)))

    def _record_call(self) -> None:
        self.call_count_session += 1
        self.calls_in_current_minute.append(time.time())

    def usage(self) -> Dict[str, Any]:
        """Returns client usage statistics."""
        now = time.time()
        active_minute_calls = len([t for t in self.calls_in_current_minute if now - t < 60.0])
        return {
            "calls_total": self.call_count_session,
            "calls_this_minute": active_minute_calls,
            "estimated_spend_usd": round(self.spend_guard.total_estimated_spend_usd, 6),
            "spend_limit_usd": self.spend_guard.max_spend_usd,
        }

    def _get_from_cache(self, key_hash: str) -> Optional[Dict[str, Any]]:
        cache_file = self.cache_dir / f"{key_hash}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    logger.info("Serving response from on-disk cache: %s", key_hash)
                    return json.load(f)
            except Exception as e:
                logger.warning("Failed to read cache file %s: %s", cache_file, e)
        return None

    def _save_to_cache(self, key_hash: str, data: Dict[str, Any]) -> None:
        cache_file = self.cache_dir / f"{key_hash}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning("Failed to write cache file %s: %s", cache_file, e)

    @staticmethod
    def _detect_image_mime(image_bytes: bytes) -> str:
        """Detects whether image is JPEG or PNG."""
        if image_bytes.startswith(b"\xff\xd8"):
            return "image/jpeg"
        return "image/png"

    async def _post_with_retry(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """Makes an HTTP POST with exponential backoff on 429 and 5xx."""
        await self._enforce_limits()
        self.spend_guard.check_can_spend(0.0001)

        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.info("Calling endpoint: %s (call #%d in session)", endpoint, self.call_count_session + 1)

        backoff = 1.0
        async with httpx.AsyncClient(timeout=timeout) as client:
            for attempt in range(1, max_retries + 1):
                try:
                    response = await client.post(url, json=payload, headers=headers)
                    self._record_call()

                    if response.status_code == 200:
                        res_json = response.json()
                        if asyncio.iscoroutine(res_json):
                            res_json = await res_json
                        usage = res_json.get("usage", {})
                        in_toks = usage.get("prompt_tokens", 0)
                        out_toks = usage.get("completion_tokens", 0)
                        cached_toks = usage.get("prompt_tokens_details", {}).get("cached_tokens", 0)
                        cost = self.spend_guard.estimate_spark_cost(in_toks, out_toks, cached_toks)
                        self.spend_guard.record_spend(cost)
                        return res_json

                    if response.status_code == 429 or 500 <= response.status_code < 600:
                        retry_after = response.headers.get("Retry-After")
                        wait_time = float(retry_after) if retry_after else backoff
                        logger.warning(
                            "HTTP %d from %s. Retry attempt %d/%d after %.2fs",
                            response.status_code,
                            endpoint,
                            attempt,
                            max_retries,
                            wait_time,
                        )
                        if attempt == max_retries:
                            response.raise_for_status()
                        await asyncio.sleep(wait_time)
                        backoff *= 2.0
                    else:
                        response.raise_for_status()

                except (httpx.TimeoutException, httpx.NetworkError) as err:
                    logger.warning("Network/Timeout error on %s: %s (attempt %d/%d)", endpoint, err, attempt, max_retries)
                    if attempt == max_retries:
                        raise
                    await asyncio.sleep(backoff)
                    backoff *= 2.0

        raise RuntimeError(f"Failed to post to {endpoint} after {max_retries} attempts.")

    async def parse_procedure(self, text: str) -> ProcedureParseResult:
        cache_key = self.hash_inputs("parse_procedure", text)
        cached = self._get_from_cache(cache_key)
        if cached:
            return ProcedureParseResult.model_validate(cached)

        messages = [
            {"role": "system", "content": self.prompt_parse},
            {"role": "user", "content": f"Procedure text:\n{text}"},
        ]
        payload = {
            "model": SPARK_MODEL,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
        }

        try:
            data = await self._post_with_retry(CHAT_PATH, payload)
            content = data["choices"][0]["message"]["content"]
            parsed_json = json.loads(content)
            result = ProcedureParseResult(
                title=parsed_json.get("title", "Extracted Procedure"),
                steps=[ProcedureStep.model_validate(s) for s in parsed_json.get("steps", [])],
                source="real",
                confidence=0.95,
            )
            self._save_to_cache(cache_key, result.model_dump())
            return result
        except Exception as e:
            logger.error("parse_procedure failed: %s", e)
            raise

    async def judge_frame(
        self,
        image_bytes: bytes,
        step: ProcedureStep,
        context: Dict[str, Any],
    ) -> VerdictResult:
        cache_key = self.hash_inputs("judge_frame", image_bytes, step.id, context)
        cached = self._get_from_cache(cache_key)
        if cached:
            return VerdictResult.model_validate(cached)

        prompt = self.prompt_judge.format(
            step_id=step.id,
            step_order=step.order,
            instruction=step.instruction,
            expected_elements=", ".join(step.expected_elements),
            success_condition=step.success_condition,
            forbidden_actions=", ".join(step.forbidden_actions),
            risk=step.risk,
            completed=json.dumps(context.get("completed", [])),
            all_steps=json.dumps(context.get("all_steps", [])),
            recent_decisions=json.dumps(context.get("recent_decisions", [])),
        )

        mime_type = self._detect_image_mime(image_bytes)
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{b64_image}"},
                    },
                ],
            }
        ]
        payload = {
            "model": SPARK_MODEL,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
        }

        for retry in range(2):
            try:
                data = await self._post_with_retry(CHAT_PATH, payload)
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                result = VerdictResult(
                    step_id=step.id,
                    status=parsed.get("status", "uncertain"),
                    observed_step_ids=parsed.get("observed_step_ids", []),
                    evidence=parsed.get("evidence", "Visual verification complete."),
                    warning_text=parsed.get("warning_text"),
                    confidence=float(parsed.get("confidence", 0.5)),
                    source="real",
                )
                self._save_to_cache(cache_key, result.model_dump())
                return result
            except Exception as e:
                logger.warning("judge_frame retry %d failed: %s", retry, e)
                if retry == 1:
                    return VerdictResult(
                        step_id=step.id,
                        status="uncertain",
                        observed_step_ids=[],
                        evidence=f"Model output invalid or failed: {e}",
                        warning_text=None,
                        confidence=0.0,
                        source="real",
                    )

    async def locate_elements(
        self,
        image_bytes: bytes,
        prompts: List[str],
    ) -> LocateElementsResult:
        cache_key = self.hash_inputs("locate_elements", image_bytes, prompts)
        cached = self._get_from_cache(cache_key)
        if cached:
            return LocateElementsResult.model_validate(cached)

        mime_type = self._detect_image_mime(image_bytes)
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        payload = {
            "model": SAM_MODEL,
            "image": f"data:{mime_type};base64,{b64_image}",
            "prompts": prompts,
        }

        try:
            data = await self._post_with_retry(SEGMENT_PATH, payload)
            sam_cost = self.spend_guard.estimate_sam_cost(1)
            self.spend_guard.record_spend(sam_cost)

            elements = []
            for item in data.get("elements", []):
                elements.append(
                    BoundingBox(
                        label=item.get("label", "element"),
                        box_2d=item.get("box_2d", [0, 0, 0, 0]),
                        confidence=item.get("confidence", 0.9),
                    )
                )
            result = LocateElementsResult(elements=elements, source="real")
            self._save_to_cache(cache_key, result.model_dump())
            return result
        except Exception as e:
            logger.warning("SAM 3.1 element detection unavailable or failed: %s. Degrading gracefully.", e)
            return LocateElementsResult(elements=[], source="real")

    async def transcribe_audio(self, audio_bytes: bytes) -> TranscriptionResult:
        cache_key = self.hash_inputs("transcribe_audio", audio_bytes)
        cached = self._get_from_cache(cache_key)
        if cached:
            return TranscriptionResult.model_validate(cached)

        await self._enforce_limits()
        b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
        payload = {
            "model": VOICE_MODEL,
            "audio": b64_audio,
        }
        try:
            data = await self._post_with_retry(VOICE_PATH, payload)
            duration = float(data.get("duration", 5.0))
            cost = self.spend_guard.estimate_voice_cost(duration)
            self.spend_guard.record_spend(cost)

            result = TranscriptionResult(
                text=data.get("text", ""),
                language=data.get("language", "en"),
                duration_seconds=duration,
                source="real",
            )
            self._save_to_cache(cache_key, result.model_dump())
            return result
        except Exception as e:
            logger.warning("Voice transcribe unavailable: %s", e)
            return TranscriptionResult(text="", duration_seconds=0.0, source="real")

    async def generate_export(self, procedure: ProcedureParseResult) -> ExportResult:
        messages = [
            {
                "role": "user",
                "content": f"Generate a clean SOP documentation markdown for this procedure: {procedure.model_dump_json()}",
            }
        ]
        payload = {
            "model": SPARK_MODEL,
            "messages": messages,
        }
        data = await self._post_with_retry(CHAT_PATH, payload)
        content = data["choices"][0]["message"]["content"]
        return ExportResult(
            formatted_document=content,
            format_type="markdown",
            source="real",
        )

    def usage(self) -> Dict[str, Any]:
        return {
            "calls_total": self.call_count_session,
            "calls_this_minute": len(self.calls_in_current_minute),
            "estimated_spend_usd": round(self.spend_guard.total_estimated_spend_usd, 4),
            "spend_limit_usd": self.spend_guard.max_spend_usd,
        }
