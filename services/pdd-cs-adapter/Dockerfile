# 拼多多客服适配器服务
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8003 \
    PLAYWRIGHT_BROWSERS_PATH=/app/.cache/ms-playwright

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg chromium chromium-driver curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium

COPY . .

RUN mkdir -p /app/data /app/logs && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8003

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
