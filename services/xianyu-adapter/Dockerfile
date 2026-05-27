# 闲鱼适配器服务
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8004

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install playwright && \
    playwright install-deps && \
    playwright install chromium

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data/cookies /app/data/logs /app/data/screenshots && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8004

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
