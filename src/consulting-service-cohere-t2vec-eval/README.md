# Consulting RAG Service

FastAPI service providing two independent knowledge stores — a **global PDF knowledge base** and per-machine **window event stores** — backed by ChromaDB and an LLM.

---

## Architecture

```
┌───────────────────────────────────────────────────────────┐
│                     FastAPI  /rag/*                        │
├──────────────────────┬────────────────────────────────────┤
│  Global KB           │  Per-machine KB                    │
│  (PDF / TXT docs)    │  (window events)                   │
│  collection: global  │  collection: machine_{id}          │
│  chunk: 800/100      │  chunk: 400/60                     │
└──────────────────────┴────────────────────────────────────┘
           │                         │
      ChromaDB                  ChromaDB
           └───────── Embedder ──────┘
                          │
                       LLMClient
```

---

## Endpoints

### Global KB

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/rag/ingest` | Upload PDF/TXT to global KB (omit `machine_id`) |
| `POST` | `/rag/ask` | Ask a question against the global KB |

### Machine KB

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/rag/ingest` | Upload PDF/TXT to a machine collection (`?machine_id=X`) |
| `POST` | `/rag/ingest-window` | Ingest a window event **with** a `reason` annotation |
| `POST` | `/rag/machine-query` | Query with a live window snapshot **without** a reason → returns best-matching stored reasons |
| `POST` | `/rag/diagnose` | Full LLM diagnosis from sensor data |

### Utility

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/rag/status` | Collection health + all chunks |
| `GET` | `/rag/chunks` | Paginated chunk listing |
| `GET` | `/rag/collections` | All collection names |
| `DELETE` | `/rag/pdf/{filename}` | Remove file + its chunks |
| `DELETE` | `/rag/chunks` | Delete by filter or IDs |
| `POST` | `/rag/reset` | Wipe an entire collection |
| `POST` | `/rag/switch-model` | Switch active LLM model |

---

## machine-query  (new)

`POST /rag/machine-query`

Send a **live** window snapshot identical to `ingest-window` but **without** a `reason` field.  The service:

1. Builds the same chunk text that would have been stored at ingest time (using `window_event_to_chunks`).
2. Queries the machine's ChromaDB collection for the `top_k` most similar stored chunks.
3. Extracts the `reason` annotation that was stored with each matching chunk.
4. Returns all matches ranked by cosine distance plus `best_reason` (rank-1 match).

### Request body

```json
{
  "machine_id":     "pump_01",
  "label":          "bearing_fault",
  "rul":            120.5,
  "window_sliding": [
    {"vibration": 4.2, "temp": 82.1, "rpm": 1490},
    {"vibration": 4.5, "temp": 83.0, "rpm": 1485}
  ],
  "message_id":     "abc-123",
  "timestamp":      1717000000.0,
  "top_k":          5
}
```

### Response

```json
{
  "machine_id":    "pump_01",
  "message_id":    "abc-123",
  "query_text":    "Machine pump_01 window event. Label: bearing_fault. RUL: 120.5 ...",
  "best_reason":   "High vibration due to worn bearing race",
  "best_distance": 0.0821,
  "matches": [
    {
      "rank":          1,
      "distance":      0.0821,
      "source":        "window:pump_01",
      "stored_reason": "High vibration due to worn bearing race",
      "text_preview":  "Machine pump_01 window event. Label: bearing_fault...",
      "full_text":     "..."
    }
  ]
}
```

---

## Column-name normalisation

Sensor data arriving with non-standard column names is automatically resolved to canonical names **before** embedding.  This ensures the query vector and stored vectors are always in the same semantic space regardless of which upstream system produced the data.

### Examples

| Incoming column | Canonical | Displayed as | Unit |
|----------------|-----------|--------------|------|
| `Ia`, `amp`, `motor_current` | `current` | "current" | A |
| `T1`, `temp_1`, `tmp` | `temperature` | "temperature" | °C |
| `press_hyd`, `hyd_press` | `hydraulic_pressure` | "hydraulic pressure" | bar |
| `vib`, `vibr` | `vibration` | "vibration" | mm/s RMS |
| `rpm_motor`, `motor_rpm` | `motor_speed` | "motor speed" | RPM |
| `n`, `shaft_speed` | `rpm` | "rpm" | RPM |
| `p`, `p1`, `oil_press` | `pressure` / `oil_pressure` | "pressure" | bar |

Add new aliases in `services/sensor_normalizer.py` → `_ALIAS_MAP`.

---

## ingest-window vs machine-query

| Field | `ingest-window` | `machine-query` |
|-------|-----------------|-----------------|
| `machine_id` | ✅ | ✅ |
| `label` | ✅ | ✅ |
| `rul` | ✅ | ✅ |
| `window_sliding` | ✅ | ✅ |
| `message_id` | ✅ | ✅ |
| `timestamp` | ✅ | ✅ |
| `reason` | ✅ stored in chunk | ❌ omitted — returned from best match |
| `top_k` | ❌ | ✅ controls how many matches to return |
| **Writes to DB** | ✅ | ❌ read-only |
| **Returns reasons** | ❌ | ✅ `best_reason` + `matches[].stored_reason` |

---

## Quick start

```bash
cp .env.example .env
# edit .env: set LLM_URL, CHROMA_PATH, etc.

pip install -r requirements.txt
uvicorn main:app --reload
```

Swagger UI: http://localhost:8000/docs
