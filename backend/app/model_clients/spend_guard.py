import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("screenguard.spend_guard")


class SpendLimitReached(Exception):
    """Raised when the estimated model spend exceeds MAX_ESTIMATED_SPEND_USD."""
    pass


class SpendGuard:
    """Tracks estimated spending across model calls and prevents overspend."""

    def __init__(
        self,
        max_spend_usd: float = 100.0,
        pricing_file_path: Optional[str] = None
    ) -> None:
        self.max_spend_usd = max_spend_usd
        self.total_estimated_spend_usd = 0.0
        self.pricing: Dict[str, Any] = self._load_pricing(pricing_file_path)

    def _load_pricing(self, path_str: Optional[str]) -> Dict[str, Any]:
        default_pricing = {
            "muse_spark": {
                "standard": {
                    "input_per_million": 1.25,
                    "output_per_million": 4.25,
                    "cached_input_per_million": 0.15
                },
                "contributor": {
                    "input_per_million": 0.10,
                    "output_per_million": 0.20,
                    "cached_input_per_million": 0.002
                }
            },
            "muse_voice_transcribe": {
                "audio_per_second": 0.00005
            },
            "sam_3_1": {
                "per_image": 0.01
            }
        }
        if not path_str:
            return default_pricing

        path = Path(path_str)
        if not path.exists():
            # Try workspace root
            root_path = Path(__file__).resolve().parent.parent.parent.parent / "config" / "pricing.json"
            if root_path.exists():
                path = root_path

        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("Could not read pricing.json from %s: %s. Using default pricing.", path, e)

        return default_pricing

    def estimate_spark_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0,
        mode: str = "standard"
    ) -> float:
        spark_pricing = self.pricing.get("muse_spark", {}).get(mode, {})
        in_rate = spark_pricing.get("input_per_million", 1.25) / 1_000_000.0
        out_rate = spark_pricing.get("output_per_million", 4.25) / 1_000_000.0
        cached_rate = spark_pricing.get("cached_input_per_million", 0.15) / 1_000_000.0

        non_cached_input = max(0, input_tokens - cached_tokens)
        cost = (non_cached_input * in_rate) + (cached_tokens * cached_rate) + (output_tokens * out_rate)
        return cost

    def estimate_sam_cost(self, images_count: int = 1) -> float:
        sam_pricing = self.pricing.get("sam_3_1", {})
        per_img = sam_pricing.get("per_image", 0.01)
        return images_count * per_img

    def estimate_voice_cost(self, duration_seconds: float) -> float:
        voice_pricing = self.pricing.get("muse_voice_transcribe", {})
        per_sec = voice_pricing.get("audio_per_second", 0.00005)
        return duration_seconds * per_sec

    def record_spend(self, cost_usd: float) -> float:
        if self.total_estimated_spend_usd + cost_usd > self.max_spend_usd:
            msg = (
                f"MAX_ESTIMATED_SPEND_USD ({self.max_spend_usd:.2f}) reached! "
                f"Attempted addition: ${cost_usd:.4f}, Current total: ${self.total_estimated_spend_usd:.4f}"
            )
            logger.error(msg)
            raise SpendLimitReached(msg)

        self.total_estimated_spend_usd += cost_usd
        logger.info("Spend recorded: +$%.6f (Total: $%.4f / $%.2f)", cost_usd, self.total_estimated_spend_usd, self.max_spend_usd)
        return self.total_estimated_spend_usd

    def check_can_spend(self, anticipated_cost_usd: float = 0.001) -> None:
        if self.total_estimated_spend_usd + anticipated_cost_usd > self.max_spend_usd:
            raise SpendLimitReached(
                f"MAX_ESTIMATED_SPEND_USD reached. Spend: ${self.total_estimated_spend_usd:.4f}, Limit: ${self.max_spend_usd:.2f}"
            )
