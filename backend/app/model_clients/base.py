import base64
import hashlib
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ProcedureStep(BaseModel):
    id: str
    order: int
    instruction: str
    expected_elements: List[str] = Field(default_factory=list)
    success_condition: str
    forbidden_actions: List[str] = Field(default_factory=list)
    depends_on: List[str] = Field(default_factory=list)
    risk: Literal["low", "high"] = "low"


class ProcedureParseResult(BaseModel):
    title: str
    steps: List[ProcedureStep]
    source: Literal["real", "mock"] = "mock"
    confidence: float = 1.0


class BoundingBox(BaseModel):
    label: str
    box_2d: List[float] = Field(description="Normalized coordinates [ymin, xmin, ymax, xmax] between 0.0 and 1.0")
    confidence: float = 1.0


class LocateElementsResult(BaseModel):
    elements: List[BoundingBox] = Field(default_factory=list)
    source: Literal["real", "mock"] = "mock"


class VerdictResult(BaseModel):
    step_id: str
    status: Literal["done", "in_progress", "wrong", "uncertain"]
    observed_step_ids: List[str] = Field(default_factory=list)
    evidence: str
    warning_text: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    source: Literal["real", "mock"] = "mock"


class TranscriptionResult(BaseModel):
    text: str
    language: str = "en"
    duration_seconds: float = 0.0
    source: Literal["real", "mock"] = "mock"


class ExportResult(BaseModel):
    formatted_document: str
    format_type: str = "markdown"
    source: Literal["real", "mock"] = "mock"


class ModelClient(ABC):
    """Abstract interface for all model interactions."""

    @abstractmethod
    async def parse_procedure(self, text: str) -> ProcedureParseResult:
        """Parses written procedure text into structured steps."""
        pass

    @abstractmethod
    async def judge_frame(
        self,
        image_bytes: bytes,
        step: ProcedureStep,
        context: Dict[str, Any]
    ) -> VerdictResult:
        """Judges whether a frame satisfies, progresses, violates, or skips a procedure step."""
        pass

    @abstractmethod
    async def locate_elements(
        self,
        image_bytes: bytes,
        prompts: List[str]
    ) -> LocateElementsResult:
        """Locates visual UI elements via text prompts."""
        pass

    @abstractmethod
    async def transcribe_audio(self, audio_bytes: bytes) -> TranscriptionResult:
        """Transcribes spoken procedure audio into text."""
        pass

    @abstractmethod
    async def generate_export(self, procedure: ProcedureParseResult) -> ExportResult:
        """Generates an exportable document from procedure and trace."""
        pass

    def usage(self) -> Dict[str, Any]:
        """Returns spend and call statistics."""
        return {
            "calls_total": 0,
            "calls_this_minute": 0,
            "estimated_spend_usd": 0.0,
            "spend_limit_usd": 100.0,
        }

    @staticmethod
    def hash_inputs(*args: Any) -> str:
        """Deterministic sha256 hash helper for caching."""
        hasher = hashlib.sha256()
        for item in args:
            if isinstance(item, bytes):
                hasher.update(item)
            elif isinstance(item, str):
                hasher.update(item.encode("utf-8"))
            elif isinstance(item, BaseModel):
                hasher.update(item.model_dump_json().encode("utf-8"))
            else:
                hasher.update(str(item).encode("utf-8"))
        return hasher.hexdigest()
