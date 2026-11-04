from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app.api.routes import router as api_router
from backend.app.api.frames import router as frames_router
from backend.app.core.config import settings
from backend.app.model_clients.factory import get_model_client

app = FastAPI(title="ScreenGuard Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(frames_router)


class ModelInfo(BaseModel):
    provider: str
    vision_model: str
    text_model: str
    family: str


class HealthResponse(BaseModel):
    status: str
    mode: str
    model_info: ModelInfo


@app.get("/api/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    client = get_model_client()
    info = client.model_info() if hasattr(client, "model_info") else {
        "provider": settings.PROVIDER,
        "vision_model": settings.GROQ_VISION_MODEL if settings.PROVIDER == "groq" else "muse-spark-1.3",
        "text_model": settings.GROQ_TEXT_MODEL if settings.PROVIDER == "groq" else "muse-spark-1.3",
        "family": "meta" if settings.PROVIDER in ["meta", "baseten"] else "other",
    }
    return HealthResponse(
        status="ok",
        mode=settings.MODE,
        model_info=ModelInfo(**info),
    )
