FROM python:3.11-slim

WORKDIR /app

# System deps for scipy (MAT file support)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default: run the batch ingestion once and exit
CMD ["python", "main.py"]

# To run the HTTP API instead:
# CMD ["uvicorn", "api.routes:app", "--host", "0.0.0.0", "--port", "8000"]
