# Hermes控制中心服务
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc postgresql-client curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/reports /app/logs /app/skills && \
    useradd -m -u 1000 hermes && \
    chown -R hermes:hermes /app
USER hermes

EXPOSE 8007

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8007/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007", "--workers", "4"]
