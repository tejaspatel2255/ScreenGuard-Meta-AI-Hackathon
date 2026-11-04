import base64
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import httpx

from backend.app.core.config import settings
from backend.app.model_clients.base import (
    ProcedureStep,
    VerdictResult,
)
from backend.app.model_clients.meta_client import MetaModelClient
from backend.app.model_clients.spend_guard import SpendGuard

logger = logging.getLogger("screenguard.baseten_client")


class BasetenModelClient(MetaModelClient):
    """Baseten client for the alternative judging model (meta-models/muse-spark-open-1026).

    Kept behind the exact same ModelClient interface.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        spend_guard: Optional[SpendGuard] = None,
    ) -> None:
        super().__init__(spend_guard=spend_guard)
        self.baseten_api_key = api_key or settings.BASETEN_API_KEY
        self.model_name = model_name or settings.BASETEN_MODEL
        self.baseten_url = f"https://model-{self.model_name}.api.baseten.co/production/predict"

    async def judge_frame(
        self,
        image_bytes: bytes,
        step: ProcedureStep,
        context: Dict[str, Any],
    ) -> VerdictResult:
        cache_key = self.hash_inputs("baseten_judge", image_bytes, step.id, context)
        cached = self._get_from_cache(cache_key)
        if cached:
            return VerdictResult.model_validate(cached)

        if not self.baseten_api_key:
            logger.warning("BASETEN_API_KEY missing. Falling back to base implementation.")
            return await super().judge_frame(image_bytes, step, context)

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
        payload = {
            "prompt": prompt,
            "image": b64_image,
            "temperature": 0.0,
        }

        headers = {
            "Authorization": f"Api-Key {self.baseten_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                res = await client.post(self.baseten_url, json=payload, headers=headers)
                res.raise_for_status()
                parsed = res.json()
                result = VerdictResult(
                    step_id=step.id,
                    status=parsed.get("status", "done"),
                    observed_step_ids=parsed.get("observed_step_ids", [step.id]),
                    evidence=parsed.get("evidence", "Baseten model verified step."),
                    warning_text=parsed.get("warning_text"),
                    confidence=float(parsed.get("confidence", 0.9)),
                    source="real",
                )
                self._save_to_cache(cache_key, result.model_dump())
                return result
            except Exception as e:
                logger.error("Baseten call failed: %s. Returning uncertain.", e)
                return VerdictResult(
                    step_id=step.id,
                    status="uncertain",
                    observed_step_ids=[],
                    evidence=f"Baseten error: {e}",
                    confidence=0.0,
                    source="real",
                )

    def model_info(self) -> Dict[str, str]:
        return {
            "provider": "baseten",
            "vision_model": self.model_name,
            "text_model": self.model_name,
            "family": "meta",
        }
