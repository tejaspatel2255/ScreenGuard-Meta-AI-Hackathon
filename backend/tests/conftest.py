import pytest
from backend.app.core.config import settings
from backend.app.model_clients.factory import reset_model_client


@pytest.fixture(autouse=True)
def force_mock_mode_for_tests(monkeypatch):
    """Enforce mock mode across all unit tests so tests never hit real APIs or block on rate limits."""
    monkeypatch.setattr(settings, "MODE", "mock")
    reset_model_client()
    yield
    reset_model_client()
