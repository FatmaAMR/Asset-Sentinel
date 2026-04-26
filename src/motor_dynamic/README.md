# Motor Fault Detection — Ingestion + Consumer

Reads **FILE 1.xlsx … FILE 10.xlsx** from a local Windows folder,
slices each file into windows, and publishes every window to RabbitMQ.
Your teammate runs `consumer.py` to receive and process the messages.

---

## Data columns (from your Excel files)

| Column | Meaning |
|--------|---------|
| x, y, Z | 3-axis vibration / position |
| I1, I2, I3 | 3-phase stator currents (A) |
| V1, V2, V3 | 3-phase voltages (V) |

---

## Project structure

```
motor_ingestion/
│
├── main.py              ← PRODUCER — run this to ingest files
├── consumer.py          ← CONSUMER — teammate runs this
├── docker-compose.yml   ← starts RabbitMQ only
├── requirements.txt
├── .env.example         ← copy to .env and edit
│
├── config/settings.py   ← DATA_DIR, RabbitMQ settings, window size
├── db/connection.py     ← SQLite registry (tracks ingested files)
├── schemas/models.py    ← Pydantic: MotorFaultRecord, MessageEnvelope
├── services/logic.py    ← IngestionService orchestrator
├── utils/
│   ├── file_parser.py   ← reads FILE N.xlsx → sliding windows
│   ├── helpers.py       ← label loader (LABEL DATASET.xlsx) + envelope builder
│   └── publisher.py     ← pika publisher with DLX + retry
└── api/routes.py        ← optional FastAPI (/health /status /ingest/trigger)
```

---

## Quick start (Windows)

### Step 1 — install dependencies
```cmd
pip install -r requirements.txt
```

### Step 2 — start RabbitMQ (Docker Desktop required)
```cmd
docker compose up -d
```
Open http://localhost:15672 in your browser (guest / guest) to see the queues.

### Step 3 — copy and configure .env
```cmd
copy .env.example .env
```
The default `DATA_DIR` is already set to `C:\Users\user\Downloads\27216219`.
Change it if your path is different.

### Step 4 — run the producer (ingestion)
```cmd
python main.py
```
You will see one log line per published window, e.g.:
```
2026-04-25 10:00:01 [INFO] ingestion: Processing FILE 1  label=unknown  path=...
2026-04-25 10:00:02 [INFO] ingestion:   FILE 1 done — 312 windows published
```

### Step 5 — run the consumer (your teammate)
In a **separate terminal**:
```cmd
python consumer.py
```
You will see:
```
2026-04-25 10:00:03 [INFO] consumer: [OK] FILE 1  window=    0  label=unknown      rows 0–1023  samples=1024
2026-04-25 10:00:03 [INFO] consumer: [OK] FILE 1  window=    1  label=unknown      rows 512–1535  samples=1024
```

---

## Message shape (what consumer receives)

```json
{
  "message_id": "uuid4",
  "source": "local_files",
  "published_at": "2026-04-25T10:00:01+00:00",
  "record": {
    "file_number": 1,
    "file_name": "FILE 1.xlsx",
    "fault_label": "unknown",
    "window_index": 0,
    "row_start": 0,
    "row_end": 1023,
    "x":  [...1024 floats...],
    "y":  [...1024 floats...],
    "z":  [...1024 floats...],
    "i1": [...1024 floats...],
    "i2": [...1024 floats...],
    "i3": [...1024 floats...],
    "v1": [...1024 floats...],
    "v2": [...1024 floats...],
    "v3": [...1024 floats...]
  }
}
```

---

## Using LABEL DATASET.xlsx

Put `LABEL DATASET.xlsx` in the same folder as the data files.
The file should have at least two columns:
- Column 1: file number or name (e.g. `1`, `FILE 1`, `FILE 1.xlsx`)
- Column 2: fault label (e.g. `normal`, `inner_race`, `outer_race`, `ball`)

If the label file is not found, all windows will have `fault_label = "unknown"`.

---

## Adjusting window size

In `.env`:
```
WINDOW_SIZE=1024    # number of rows per message
WINDOW_STEP=512     # overlap (512 = 50% overlap)
```

No overlap:  `WINDOW_SIZE=1024  WINDOW_STEP=1024`
Full overlap: `WINDOW_SIZE=1024  WINDOW_STEP=256`

---

## Teammate extension points

In `consumer.py`, extend the `_process()` function:

```python
def _process(envelope: MessageEnvelope) -> None:
    r = envelope.record
    # r.x, r.y, r.z   — vibration signals
    # r.i1, r.i2, r.i3 — currents
    # r.v1, r.v2, r.v3 — voltages
    # r.fault_label, r.file_number, r.window_index

    features = extract_features(r)       # your FFT / RMS / kurtosis
    validate(features)                   # Pydantic range checks
    write_to_timescaledb(features)       # store clean data
```

---

## RabbitMQ queues

| Queue | Purpose |
|-------|---------|
| `motor.raw` | Main queue — consumer reads from here |
| `motor.failed` | Dead-letter — messages that failed after 3 retries |

View both at http://localhost:15672 → Queues tab.
