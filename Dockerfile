FROM python:3.11-slim

WORKDIR /app

# System deps for ML models
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Python deps
COPY backend/requirements.txt /app/backend/requirements.txt
COPY backend/rag_requirements.txt /app/backend/rag_requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt && \
    pip install --no-cache-dir -r /app/backend/rag_requirements.txt && \
    pip install pyarrow pyyaml keybert pytest

# Copy backend
COPY backend/ /app/backend/
COPY data_collection/ /app/data_collection/
COPY pipelines/ /app/pipelines/
COPY models/ /app/models/
COPY alerts/ /app/alerts/
COPY reports/ /app/reports/
COPY config/ /app/config/
COPY output/ /app/output/

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
