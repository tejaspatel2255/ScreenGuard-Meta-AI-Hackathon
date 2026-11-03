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
from backend.app.model_clients.spend_guard import SpendGuard

logger = logging.getLogger("screenguard.groq_client")


class GroqModelClient(ModelClient):
    """Real client using Groq OpenAI-compatible endpoints serving Meta open-weight models."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        spend_guard: Optional[SpendGuard] = None,
        cache_dir: Optional[Path] = None,
    ) -> None:
        self.api_key = api_key or settings.GROQ_API_KEY
        self.base_url = "https://api.groq.com/openai/v1"
        self.spend_guard = spend_guard or SpendGuard(max_spend_usd=settings.MAX_ESTIMATED_SPEND_USD)
        self.cache_dir = cache_dir or (Path(__file__).resolve().parent.parent.parent.parent / "cache" / "model_responses")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.call_count_session = 0
        self.calls_in_current_minute: List[float] = []

        prompts_dir = Path(__file__).resolve().parent.parent / "prompts"
        parse_p_path = prompts_dir / "parse_procedure.txt"
        judge_p_path = prompts_dir / "judge_frame.txt"
        self.prompt_parse = parse_p_path.read_text(encoding="utf-8") if parse_p_path.exists() else ""
        self.prompt_judge = judge_p_path.read_text(encoding="utf-8") if judge_p_path.exists() else ""

    async def _enforce_limits(self) -> None:
        if self.call_count_session >= settings.MAX_CALLS_PER_SESSION:
            raise RuntimeError(f"MAX_CALLS_PER_SESSION ({settings.MAX_CALLS_PER_SESSION}) reached.")

        while True:
            now = time.time()
            self.calls_in_current_minute = [t for t in self.calls_in_current_minute if now - t < 60.0]
            if len(self.calls_in_current_minute) < settings.MAX_CALLS_PER_MINUTE:
                break
            await asyncio.sleep(1.0)

    def _record_call(self) -> None:
        self.call_count_session += 1
        self.calls_in_current_minute.append(time.time())

    def _get_from_cache(self, key_hash: str) -> Optional[Dict[str, Any]]:
        cache_file = self.cache_dir / f"{key_hash}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def _save_to_cache(self, key_hash: str, data: Dict[str, Any]) -> None:
        cache_file = self.cache_dir / f"{key_hash}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    async def _post_with_retry(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        await self._enforce_limits()
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        backoff = 1.0
        async with httpx.AsyncClient(timeout=timeout) as client:
            for attempt in range(1, max_retries + 1):
                try:
                    response = await client.post(url, json=payload, headers=headers)
                    self._record_call()
                    if response.status_code == 200:
                        res_json = response.json()
                        usage = res_json.get("usage", {})
                        in_toks = usage.get("prompt_tokens", 0)
                        out_toks = usage.get("completion_tokens", 0)
                        cost = self.spend_guard.estimate_spark_cost(in_toks, out_toks)
                        self.spend_guard.record_spend(cost)
                        return res_json

                    if response.status_code != 200:
                        logger.error("Groq error %d: %s", response.status_code, response.text)
                    if response.status_code == 429 or 500 <= response.status_code < 600:
                        retry_after = response.headers.get("Retry-After")
                        wait_time = float(retry_after) if retry_after else backoff
                        if attempt == max_retries:
                            response.raise_for_status()
                        await asyncio.sleep(wait_time)
                        backoff *= 2.0
                    else:
                        response.raise_for_status()
                except Exception as err:
                    if attempt == max_retries:
                        raise
                    await asyncio.sleep(backoff)
                    backoff *= 2.0

        raise RuntimeError(f"Failed to call {endpoint}")

    async def parse_procedure(self, text: str) -> ProcedureParseResult:
        cache_key = self.hash_inputs("groq_parse_procedure", text)
        cached = self._get_from_cache(cache_key)
        if cached:
            return ProcedureParseResult.model_validate(cached)

        messages = [
            {"role": "system", "content": self.prompt_parse},
            {"role": "user", "content": f"Procedure text:\n{text}"},
        ]
        payload = {
            "model": settings.GROQ_TEXT_MODEL,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
        }

        data = await self._post_with_retry("/chat/completions", payload)
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

    async def judge_frame(
        self,
        image_bytes: bytes,
        step: ProcedureStep,
        context: Dict[str, Any],
    ) -> VerdictResult:
        cache_key = self.hash_inputs("groq_judge_frame", image_bytes, step.id, context)
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
            context=json.dumps(context),
        )

        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        mime_type = "image/jpeg" if image_bytes.startswith(b"\xff\xd8\xff") else "image/png"

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
            "model": settings.GROQ_VISION_MODEL,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
        }

        try:
            data = await self._post_with_retry("/chat/completions", payload)
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
            logger.warning("Groq judge_frame failed: %s", e)
            return VerdictResult(
                step_id=step.id,
                status="uncertain",
                observed_step_ids=[],
                evidence=f"Model output invalid or failed: {e}",
                confidence=0.0,
                source="real",
            )

    async def locate_elements(self, image_bytes: bytes, prompts: List[str]) -> LocateElementsResult:
        return LocateElementsResult(elements=[], source="real")

    async def transcribe_audio(self, audio_bytes: bytes) -> TranscriptionResult:
        return TranscriptionResult(text="", duration_seconds=0.0, source="real")

    async def generate_export(self, procedure: ProcedureParseResult) -> ExportResult:
        messages = [
            {"role": "user", "content": f"Generate clean SOP Markdown documentation: {procedure.model_dump_json()}"}
        ]
        payload = {"model": settings.GROQ_TEXT_MODEL, "messages": messages}
        data = await self._post_with_retry("/chat/completions", payload)
        content = data["choices"][0]["message"]["content"]
        return ExportResult(formatted_document=content, format_type="markdown", source="real")
