# Asset-Sentinel: proactive industrial maintenance Ecosystem 🛡️🏭

Asset-Sentinel is an end-to-end, proactive industrial maintenance platform designed to predict equipment failures and optimize maintenance cycles. By leveraging a hybrid AI approach, it combines high-precision numerical forecasting with generative intelligence for diagnostics.

---

## System Architecture
The project follows a **Microservices Architecture** with each service organized using a **Simple Layered Design**. Communication is handled via **RabbitMQ** (Event-Driven) for real-time sensor data and **REST APIs** for user interactions.

### Core Services:
* **Forecasting Service**: High-speed RUL (Remaining Useful Life) prediction using **PatchTST**.
* **Consulting Service**: RAG-based diagnostic engine for technical manuals and proactive maintenance suggestions.
* **Notification Service**: Multi-channel alerting system with an **Acknowledge Handler** for human-in-the-loop feedback.
* **Querying Service**: Natural language interface using **Text-to-SQL** for seamless data exploration.
* **Reporting & Visualization**: Real-time dashboards and historical performance analytics.
* **Managerial Service**: Factory hierarchy, user roles, and system configuration management.
  
<img width="5689" height="2405" alt="GP General Thoughts" src="https://github.com/user-attachments/assets/4afbc8f0-073f-451f-b322-1ff5d9e51ded" />

---

## 🛠️ Tech Stack
* **Backend**: Python 3.10+, FastAPI.
* **Intelligence**: PyTorch (Transformers), LangChain, Llama-3.2.
* **Data**: InfluxDB (Time-series), PostgreSQL (Relational), Qdrant/Chroma (Vector DB).
* **Infrastructure**: RabbitMQ (Broker), Docker & Docker-Compose.

---

## Directory Structure
Each service in `src/` follows this layout:
- `api/`: Endpoint definitions and controllers.
- `models/`: AI model architectures and weights.
- `services/`: Business logic (Validation, Uncertainty checking).
- `db/`: Database connectors and repository logic.
- `utils/`: Data preprocessing and helper functions.
- `schemas/`: Pydantic models for data validation.

---

## Getting Started
1. **Clone the repo**: `git clone https://github.com/FatmaAMR/Asset-Sentinel/`
2. **Environment Setup**: Copy `.env.example` to `.env` in each service.
3. **Infrastructure**: Run `docker-compose up -d` in the `deployments/` directory.
4. **Development**: Use `pip install -r requirements.txt` for local service development.

---
