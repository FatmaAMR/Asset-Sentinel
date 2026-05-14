import logging
from services.model_loader import loader
from config.settings import settings

logger = logging.getLogger(__name__)


class ModelRouter:
    """
    Resolves which model to use for a given request.

    Priority order:
    1. Explicit model key passed in the request body
    2. Currently active model in loader
    3. settings.default_model (fallback)
    """

    def resolve(self, requested_model: str | None) -> str:
        if requested_model:
            if requested_model not in settings.model_registry:
                raise ValueError(
                    f"Requested model '{requested_model}' is not in the registry. "
                    f"Available: {list(settings.model_registry.keys())}"
                )
            return requested_model

        if loader.current_model_name:
            return loader.current_model_name

        return settings.default_model

    def ensure_loaded(self, model_key: str) -> None:
        """Load the model if it is not already the active one."""
        if loader.current_model_name != model_key:
            logger.info(f"Router switching model to '{model_key}'")
            loader.load(model_key)


router = ModelRouter()
