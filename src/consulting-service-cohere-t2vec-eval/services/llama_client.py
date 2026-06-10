"""
services/llama_client.py
─────────────────────────
Async wrapper around a local Ollama model.
All settings come from config.py / .env
"""

import logging
import httpx
from config import settings

logger = logging.getLogger("llama_client")


class LlamaClient:

    async def complete(self, prompt: str) -> str:
        options = {
            "temperature":    settings.llm_temperature,
            "num_predict":    settings.llm_num_predict,
            "num_ctx":        settings.llm_num_ctx,
            "repeat_penalty": settings.llm_repeat_penalty,
        }

        async with httpx.AsyncClient(timeout=settings.llama_timeout) as client:
            try:
                response = await client.post(
                    f"{settings.ollama_url}/api/generate",
                    json={
                        "model":   settings.ollama_model,
                        "prompt":  prompt,
                        "stream":  False,
                        "options": options,
                    },
                )
                response.raise_for_status()
                return response.json()["response"].strip()

            except httpx.ConnectError:
                logger.error("Ollama not running at %s", settings.ollama_url)
                raise RuntimeError(
                    f"Cannot connect to Ollama at {settings.ollama_url}. "
                    "Run: ollama serve"
                )
            except httpx.TimeoutException:
                raise RuntimeError(
                    f"Ollama timed out after {settings.llama_timeout}s. "
                    "Try a faster model "
                )
