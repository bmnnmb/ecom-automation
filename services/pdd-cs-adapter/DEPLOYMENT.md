# 拼多多客服自动化服务部署指南

本文档覆盖本地开发、Docker 部署，以及拼多多扫码登录所需的最小配置。

## 快速开始

### 1. 本地开发

```bash
# 克隆或进入项目目录
cd ~/ecom-automation/services/pdd-cs-adapter

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install chromium

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入实际配置

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8003
```

### 2. 使用启动脚本

```bash
# 赋予执行权限
chmod +x start.sh

# 安装依赖并启动
./start.sh --install

# 或者直接启动
./start.sh

# 指定端口
./start.sh --port 8080
```

### 3. 使用Docker部署

```bash
# 构建镜像
docker build -t pdd-cs-adapter .

# 运行容器
docker run -d \
  --name pdd-cs-adapter \
  -p 8003:8003 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  pdd-cs-adapter
```

### 4. 使用Docker Compose

```bash
# 启动所有服务
docker compose up -d pdd-cs-adapter

# 查看日志
docker compose logs -f pdd-cs-adapter

# 停止服务
docker compose stop pdd-cs-adapter
```

## 配置说明

### 扫码登录最小配置

在 `.env` 文件中配置以下变量：

```env
# 二维码截图与浏览器会话目录
PDD_DATA_DIR=/app/data

# 浏览器配置
BROWSER_HEADLESS=true
```

### 可选配置

```env
# 拼多多开放平台 API 凭证（仅开放平台接口场景需要）
PDD_CLIENT_ID=your_client_id
PDD_CLIENT_SECRET=your_client_secret
PDD_ACCESS_TOKEN=your_access_token

# 自动回复配置
AUTO_REPLY_ENABLED=true
AUTO_REPLY_DELAY=2.0

# 数据库配置
DATABASE_URL=sqlite:///./data/pdd_cs.db

# Redis配置（可选）
REDIS_URL=redis://localhost:6379/0
```

说明：
- 本地扫码登录不要求 `PDD_CLIENT_ID` / `PDD_CLIENT_SECRET`
- 若使用 Docker Compose，请确保 `PDD_DATA_DIR` 与 `/app/data` 挂载保持一致
- `pdd_storage_state.json` 和 `pdd_login.png` 都会写入 `PDD_DATA_DIR`

## API文档

启动服务后访问：
- Swagger UI: http://localhost:8003/docs
- ReDoc: http://localhost:8003/redoc

## 监控和日志

### 健康检查

```bash
curl http://localhost:8003/health
```

### 系统状态

```bash
curl http://localhost:8003/api/v1/system/status
```

### 拼多多扫码登录验证

```bash
# 生成二维码
curl -X POST http://localhost:8003/api/v1/system/pdd-login/start

# 查看登录状态
curl http://localhost:8003/api/v1/system/pdd-login/status
```

### 查看日志

```bash
# Docker容器日志
docker logs pdd-cs-adapter

# 应用日志
tail -f logs/service.log
```

## 故障排除

### 1. 浏览器自动化失败

确保安装了Playwright浏览器：

```bash
playwright install chromium
```

### 2. 无法获取二维码截图

```bash
ls -la data
curl -I http://localhost:8003/api/v1/system/pdd-login/screenshot
```

- 检查 `PDD_DATA_DIR` 是否可写
- 检查服务日志中是否已成功打开拼多多工作台登录页

### 3. 连接拼多多开放平台 API 失败

检查API凭证是否正确：

```bash
curl http://localhost:8003/api/v1/system/test/pdd-connection
```

### 4. 内存不足

如果使用Docker，确保分配足够内存（至少2GB）。

## 生产环境部署建议

1. **使用反向代理**：配置Nginx或Apache作为反向代理
2. **HTTPS**：配置SSL证书
3. **进程管理**：使用systemd或supervisor管理进程
4. **监控**：配置Prometheus和Grafana监控
5. **日志管理**：配置日志轮转和集中日志收集
6. **备份**：定期备份知识库和数据库

## 安全注意事项

1. 不要将 `.env` 文件提交到版本控制
2. 定期更新依赖包
3. 使用强密码
4. 限制API访问权限
5. 定期审查日志
