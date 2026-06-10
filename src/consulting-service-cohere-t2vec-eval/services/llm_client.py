"""
llm_client.py
=============
Drop this file into your querying-service or consulting-service.
It provides a simple async client for calling master-llm-service.

Usage (querying service):
    from utils.llm_client import LLMClient
    client = LLMClient()
    text = await client.generate(
        prompt="Extract the 3 key risks from: ...",
        caller="querying",
        system_prompt="Return JSON only.",
    )

Usage (consulting service):
    text = await client.generate(
        prompt="How should I restructure my budget?",
        caller="consulting",
        system_prompt="You are a helpful financial advisor.",
    )
"""

import httpx
import os
from typing import Literal
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
MASTER_LLM_URL = os.getenv("MASTER_LLM_URL", "http://localhost:8000")
ADMIN_API_KEY   = os.getenv("MASTER_LLM_ADMIN_KEY", "gradteam")


class LLMClient:
    def __init__(self, base_url: str = MASTER_LLM_URL, timeout: float = 300.0):
        self.base_url = base_url.rstrip("/")
        self.timeout  = timeout

    # ------------------------------------------------------------------
    # Core: generate text
    # ------------------------------------------------------------------

    async def generate(
        self,
        prompt: str,
        caller: Literal["querying", "consulting", "other"] = "other",
        system_prompt: str | None = None,
        model: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> str:
        """Call /generate and return the generated text string."""
        payload = {
            "prompt":        prompt,
            "caller":        caller,
            "max_tokens":    max_tokens,
            "temperature":   temperature,
        }
        if system_prompt:
            payload["system_prompt"] = system_prompt
        if model:
            payload["model"] = model

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/generate", json=payload)
            resp.raise_for_status()
            return resp.json()["text"]

    # ------------------------------------------------------------------
    # Admin: switch model
    # ------------------------------------------------------------------

    async def switch_model(self, model_key: str) -> dict:
        """Switch the active model on master-llm-service."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/admin/switch-model",
                json={"model": model_key},
                headers={"X-Admin-Key": ADMIN_API_KEY},
            )
            resp.raise_for_status()
            return resp.json()

    # ------------------------------------------------------------------
    # Info: list available models
    # ------------------------------------------------------------------

    async def list_models(self) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self.base_url}/models")
            resp.raise_for_status()
            return resp.json()

    async def health(self) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self.base_url}/health")
            resp.raise_for_status()
            return resp.json()
