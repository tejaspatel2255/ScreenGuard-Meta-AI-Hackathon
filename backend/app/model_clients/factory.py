import logging
from backend.app.core.config import settings
from backend.app.model_clients.base import ModelClient
from backend.app.model_clients.baseten_client import BasetenModelClient
from backend.app.model_clients.meta_client import MetaModelClient
from backend.app.model_clients.mock_client import MockModelClient

logger = logging.getLogger("screenguard.factory")


def get_model_client() -> ModelClient:
    """Factory that returns the appropriate ModelClient based on MODE and PROVIDER."""
    mode = settings.MODE.lower()

    if mode == "mock":
        logger.info("Initializing MockModelClient (MODE=mock)")
        return MockModelClient()

    if mode in ["real", "replay"]:
        provider = settings.PROVIDER.lower()
        if provider == "baseten":
            logger.info("Initializing BasetenModelClient (PROVIDER=baseten)")
            return BasetenModelClient()

        logger.info("Initializing MetaModelClient (PROVIDER=meta)")
        return MetaModelClient()

    logger.warning("Unrecognized MODE='%s'. Defaulting to MockModelClient.", mode)
    return MockModelClient()
