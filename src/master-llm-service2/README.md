# master-llm-service


---

## Folder structure

```
master-llm-service/
├── api/
│   └── routes.py           # /generate, /models, /admin/switch-model
├── config/
│   └── settings.py         # All env-driven config (model registry, device, etc.)
├── db/
│   └── model_registry.py   # SQLite log of model switches (SQLAlchemy async)
├── schemas/
│   └── llm_schemas.py      # Pydantic request/response models
├── services/
│   ├── model_loader.py     # Loads / unloads HuggingFace models (singleton)
│   ├── model_router.py     # Picks which model to use per request
│   └── inference.py        # Orchestrates routing + generation
├── tests/
│   └── test_routes.py      # Pytest tests (no real model loaded)
├── utils/
│   └── llm_client.py       # Drop into querying/consulting service to call this API
├── main.py                 # FastAPI app + lifespan
├── requirements.txt
├── Dockerfile
├── pytest.ini
└── .env.example
```

---

## Setup

### 1. Install dependencies
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env — set HF_TOKEN for Llama, ADMIN_API_KEY, DEVICE
```

### 3. HuggingFace login (required for Llama)
```bash
pip install huggingface_hub
huggingface-cli login           # paste your HF token
# Also accept the Llama 3.2 license at huggingface.co/meta-llama/Llama-3.2-1B-Instruct
```
Qwen 2.5 is fully open — no login needed.

### 4. Run the service
```bash
uvicorn main:app --reload --port 8000
```

---

## API reference

### `POST /generate`
Main endpoint called by querying-service and consulting-service.

```json
{
  "prompt": "What are the top 3 risks in this report?",
  "system_prompt": "Return JSON only.",
  "caller": "querying",
  "model": null,
  "max_tokens": 512,
  "temperature": 0.7
}
```

**`caller`** options: `"querying"`, `"consulting"`, `"other"`  
**`model`** (optional): override the active model for this request only.

Response:
```json
{
  "text": "...",
  "model_used": "llama-3.2-1b",
  "tokens_generated": 87,
  "caller": "querying",
  "timestamp": "2024-01-01T12:00:00"
}
```

---

### `POST /admin/switch-model`
Switch the active model at runtime. Requires `X-Admin-Key` header.

```bash
curl -X POST http://localhost:8000/admin/switch-model \
     -H "Content-Type: application/json" \
     -H "X-Admin-Key: changeme" \
     -d '{"model": "qwen-2.5"}'
```

---

### `GET /models`
List available models and the currently active one.

```bash
curl http://localhost:8000/models
```

---

### `GET /health`
Quick liveness check.

---

## How querying-service and consulting-service call this

Copy `utils/llm_client.py` into each downstream service, then:

```python
from utils.llm_client import LLMClient

client = LLMClient(base_url="http://master-llm-service:8000")

# Querying service
result = await client.generate(
    prompt="Extract the top 3 risks from: ...",
    caller="querying",
    system_prompt="Return JSON only.",
    temperature=0.2,
)

# Consulting service
result = await client.generate(
    prompt="How should I restructure my budget?",
    caller="consulting",
    system_prompt="You are a helpful financial advisor.",
)

# Switch models (admin)
await client.switch_model("qwen-2.5")
```

Set the env var in each downstream service:
```bash
MASTER_LLM_URL=http://master-llm-service:8000
MASTER_LLM_ADMIN_KEY=changeme
```

---

## Available models

| Key | HuggingFace ID | Notes |
|-----|----------------|-------|
| `llama-3.2-1b` | `meta-llama/Llama-3.2-1B-Instruct` | Requires HF token + license acceptance |
| `qwen-2.5`     | `Qwen/Qwen2.5-1.5B-Instruct`        | Fully open, no login needed |

To add a new model, add it to `model_registry` in `config/settings.py`:
```python
model_registry: Dict[str, str] = {
    "llama-3.2-1b": "meta-llama/Llama-3.2-1B-Instruct",
    "qwen-2.5":     "Qwen/Qwen2.5-1.5B-Instruct",
    "my-new-model": "org/model-name-on-hf",   # ← add here
}
```
No other code changes needed.

---

## Run tests
```bash
pytest tests/ -v
```
Tests mock the model loader — no GPU or model download required.

---

## Docker
```bash
docker build -t master-llm-service .
docker run -p 8000:8000 \
  -e HF_TOKEN=hf_xxx \
  -e DEFAULT_MODEL=llama-3.2-1b \
  -e ADMIN_API_KEY=changeme \
  master-llm-service
```
