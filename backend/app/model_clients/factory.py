import logging
from typing import Optional
from backend.app.core.config import settings
from backend.app.model_clients.base import ModelClient
from backend.app.model_clients.baseten_client import BasetenModelClient
from backend.app.model_clients.groq_client import GroqModelClient
from backend.app.model_clients.meta_client import MetaModelClient
from backend.app.model_clients.mock_client import MockModelClient

logger = logging.getLogger("screenguard.factory")

_client_instance: Optional[ModelClient] = None
_client_mode: Optional[str] = None
_client_provider: Optional[str] = None


def get_model_client(force_new: bool = False) -> ModelClient:
    """Factory that returns a persistent singleton ModelClient based on MODE and PROVIDER."""
    global _client_instance, _client_mode, _client_provider

    mode = settings.MODE.lower()
    provider = settings.PROVIDER.lower()

    if not force_new and _client_instance is not None and _client_mode == mode and _client_provider == provider:
        return _client_instance

    if mode == "mock":
        logger.info("Initializing MockModelClient singleton (MODE=mock)")
        _client_instance = MockModelClient()
    elif mode in ["real", "replay"]:
        if provider == "groq":
            logger.info("Initializing GroqModelClient singleton (PROVIDER=groq, running Meta open-weights models)")
            _client_instance = GroqModelClient()
        elif provider == "baseten":
            logger.info("Initializing BasetenModelClient singleton (PROVIDER=baseten)")
            _client_instance = BasetenModelClient()
        else:
            logger.info("Initializing MetaModelClient singleton (PROVIDER=meta)")
            _client_instance = MetaModelClient()
    else:
        logger.warning("Unrecognized MODE='%s'. Defaulting to MockModelClient singleton.", mode)
        _client_instance = MockModelClient()

    _client_mode = mode
    _client_provider = provider
    return _client_instance


def reset_model_client() -> None:
    """Resets the singleton model client instance (useful for unit tests)."""
    global _client_instance, _client_mode, _client_provider
    _client_instance = None
    _client_mode = None
    _client_provider = None
