# 拼多多客服适配器服务
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8003 \
    PLAYWRIGHT_BROWSERS_PATH=/app/.cache/ms-playwright \
    DISPLAY=:99

WORKDIR /app

# 安装系统依赖和 Playwright 所需的库
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg curl xvfb x11vnc novnc websockify \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libasound2 libpango-1.0-0 \
    libcairo2 libatspi2.0-0 fonts-liberation fonts-unifont \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 安装 Playwright 浏览器
RUN playwright install chromium

COPY . .

RUN mkdir -p /app/data /app/logs && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8003 5900 6080

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Xvfb 提供容器内可见桌面，noVNC 让宿主机前端能打开浏览器完成滑块/短信验证。
CMD ["sh", "-c", "Xvfb :99 -screen 0 1280x720x24 & x11vnc -display :99 -forever -shared -nopw -listen 0.0.0.0 -xkb -quiet & websockify --web=/usr/share/novnc 0.0.0.0:6080 localhost:5900 & uvicorn main:app --host 0.0.0.0 --port 8003"]
