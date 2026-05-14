"""
tests/test_routes.py
====================
Run with:  pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os
from types import ModuleType

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ------------------------------------------------------------------
# Stub out heavy deps (torch, transformers) before any import
# ------------------------------------------------------------------

for mod in ["torch", "transformers"]:
    sys.modules.setdefault(mod, ModuleType(mod))

torch_stub = sys.modules["torch"]
torch_stub.float16 = "float16"
torch_stub.no_grad = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
torch_stub.cuda = MagicMock()
torch_stub.cuda.is_available = MagicMock(return_value=False)

trans_stub = sys.modules["transformers"]
trans_stub.AutoTokenizer = MagicMock()
trans_stub.AutoModelForCausalLM = MagicMock()

# ------------------------------------------------------------------
# Mock the model loader singleton BEFORE importing app modules
# ------------------------------------------------------------------

mock_loader = MagicMock()
mock_loader.current_model_name = "llama-3.2-1b"
mock_loader.generate.return_value = ("Mocked LLM output", 10)
mock_loader.load = MagicMock()

import services.model_loader
import services.model_router
import services.inference

services.model_loader.loader = mock_loader
services.model_router.loader = mock_loader
services.inference.loader    = mock_loader

with patch("db.model_registry.record_model_switch", new_callable=AsyncMock):
    from main import app

client = TestClient(app)

ADMIN_HEADERS = {"X-Admin-Key": "changeme"}


# ------------------------------------------------------------------
# Health check
# ------------------------------------------------------------------

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "active_model" in data


# ------------------------------------------------------------------
# /generate
# ------------------------------------------------------------------

def test_generate_basic():
    resp = client.post("/generate", json={
        "prompt": "Hello, how are you?",
        "caller": "consulting",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "text" in data
    assert data["caller"] == "consulting"
    assert "model_used" in data


def test_generate_with_system_prompt():
    resp = client.post("/generate", json={
        "prompt": "Extract risks from: The project may be delayed.",
        "system_prompt": "Return JSON only.",
        "caller": "querying",
        "max_tokens": 256,
        "temperature": 0.2,
    })
    assert resp.status_code == 200


def test_generate_invalid_model():
    with patch("services.model_router.router.resolve", side_effect=ValueError("bad model")):
        resp = client.post("/generate", json={
            "prompt": "test",
            "model": "nonexistent-model",
            "caller": "other",
        })
        assert resp.status_code == 400


# ------------------------------------------------------------------
# /models
# ------------------------------------------------------------------

def test_list_models():
    resp = client.get("/models")
    assert resp.status_code == 200
    data = resp.json()
    assert "active_model" in data
    assert "available_models" in data
    assert "llama-3.2-1b" in data["available_models"]
    assert "qwen-2.5" in data["available_models"]


# ------------------------------------------------------------------
# /admin/switch-model
# ------------------------------------------------------------------

def test_switch_model_success():
    with patch("api.routes.record_model_switch", new_callable=AsyncMock):
        resp = client.post(
            "/admin/switch-model",
            json={"model": "qwen-2.5"},
            headers=ADMIN_HEADERS,
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["active_model"] == "qwen-2.5"


def test_switch_model_no_key():
    resp = client.post("/admin/switch-model", json={"model": "qwen-2.5"})
    assert resp.status_code == 422  # missing required header


def test_switch_model_wrong_key():
    resp = client.post(
        "/admin/switch-model",
        json={"model": "qwen-2.5"},
        headers={"X-Admin-Key": "wrongkey"},
    )
    assert resp.status_code == 403


def test_switch_model_invalid():
    resp = client.post(
        "/admin/switch-model",
        json={"model": "gpt-999"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 400
