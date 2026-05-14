import httpx
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

OLLAMA_BASE = "http://localhost:11434"


class ModelLoader:
    """
    Talks to the local Ollama server instead of loading weights directly.
    No GPU/VRAM management needed — Ollama handles all of that.
    """

    def __init__(self):
        self.current_model_name: str | None = None

    def load(self, model_key: str) -> None:
        """
        'Loading' with Ollama just means validating the key and
        storing it. Ollama pulls the model into memory on first use.
        """
        if model_key not in settings.model_registry:
            raise ValueError(
                f"Unknown model key: '{model_key}'. "
                f"Available: {list(settings.model_registry.keys())}"
            )
        self.current_model_name = model_key
        logger.info(f"Active model set to '{model_key}' "
                    f"({settings.model_registry[model_key]})")

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> tuple[str, int]:
        """
        Call Ollama's /api/chat endpoint (sync via httpx).
        Returns (generated_text, token_count).
        """
        if not self.current_model_name:
            raise RuntimeError("No model selected. Call loader.load(model_key) first.")

        ollama_model = settings.model_registry[self.current_model_name]

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model":   ollama_model,
            "messages": messages,
            "stream":  False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        with httpx.Client(timeout=120.0) as client:
            resp = client.post(f"{OLLAMA_BASE}/api/chat", json=payload)
            resp.raise_for_status()

        data = resp.json()
        text = data["message"]["content"]
        tokens = data.get("eval_count", 0)
        return text.strip(), tokens


loader = ModelLoader()