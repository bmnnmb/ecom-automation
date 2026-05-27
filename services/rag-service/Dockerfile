# RAG知识库服务
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    RAG_SERVICE_HOST=0.0.0.0 \
    RAG_SERVICE_PORT=8006

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --shell /bin/bash appuser && \
    mkdir -p /app/data /app/indexes /app/logs && \
    chown -R appuser:appuser /app

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8006

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8006/health || exit 1

CMD ["python", "main.py"]
