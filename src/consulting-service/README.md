# Consulting Service — RAG with Llama 3.2 + ChromaDB

## Structure
```
consulting-service/
├── api/
│   └── rag_router.py        ← POST /rag/ask, POST /rag/ingest, GET /rag/status
├── db/
│   └── chroma_client.py     ← persistent ChromaDB connection
├── schemas/
│   └── rag_schemas.py       ← Pydantic request/response models
├── services/
│   ├── pdf_loader.py        ← reads PDFs → chunks
│   ├── embedder.py          ← embeds chunks into ChromaDB
│   ├── llama_client.py      ← calls Llama (Ollama local or Groq cloud)
│   └── rag_service.py       ← combines embedder + llama
├── utils/
│   └── logger.py
├── knowledge/               ← DROP YOUR PDF MANUALS HERE
├── main.py
├── requirements.txt
└── .env.example
```

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Add PDF manuals
```
knowledge/motor_manual.pdf
knowledge/bearing_guide.pdf
```

### 4. Start Llama locally (Ollama)
```bash
ollama pull llama3.2
ollama serve
```

### 5. Run the service
```bash
python main.py
```
PDFs are auto-ingested on startup.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /rag/ask | Ask a question from PDF knowledge |
| POST | /rag/ingest | Load/reload PDFs into ChromaDB |
| GET  | /rag/status | Check knowledge base size |
| GET  | /health | Service health check |

## Example

```bash
curl -X POST http://localhost:8002/rag/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "what causes bearing wear?"}'
```

## Add new PDFs later
Drop the PDF into `knowledge/` then call:
```bash
curl -X POST http://localhost:8002/rag/ingest
```
