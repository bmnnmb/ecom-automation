# 拼多多平台授权使用指南

## 功能说明

系统管理页的拼多多授权使用账号密码方案：后端打开拼多多商家后台，从 `.env` 读取 `PDD_USERNAME` / `PDD_PASSWORD` 自动填入并提交；如出现滑块、短信或扫码确认，由用户在可见浏览器中手动完成。后端检测到有效登录态后保存 session 并关闭浏览器。

Docker Compose 部署时，容器内浏览器通过 noVNC 暴露到本机 `http://localhost:6080/vnc.html`，授权弹窗会显示“打开远程浏览器”入口。

## 使用步骤

### 1. 访问系统管理页面

打开浏览器访问：`http://localhost:5173/system`

### 2. 发起拼多多授权

- 进入“店铺设置”
- 在“平台授权”卡片中找到“拼多多”
- 点击“授权”
- 在弹窗中点击“账号密码授权”

### 3. 完成验证

- 后端会自动填入 `.env` 中的账号密码并点击登录
- 如出现滑块、短信或扫码确认，由用户手动处理
- 前端每 2 秒检测一次登录状态
- 检测成功后后端保存 `pdd_storage_state.json` 并关闭浏览器

### 4. 查看授权信息

- 平台授权列表中点击拼多多的“查看”
- 或访问：`/api/v1/system/pdd-auth/page`

授权信息只展示会话文件路径、更新时间、Cookie 名称、域名和过期时间，不展示 Cookie 值。

### 5. 解绑授权

- 点击“解绑”
- 确认后后端关闭浏览器并删除已保存的 session 文件

## 后端接口

- `POST /api/v1/system/pdd-login/start` - 发起账号密码授权登录
- `GET /api/v1/system/pdd-login/status` - 查询账号密码授权登录状态
- `POST /api/v1/system/pdd-login/cancel` - 取消账号密码授权登录
- `POST /api/v1/system/pdd-login/password` - 兼容入口，同样发起账号密码授权登录
- `GET /api/v1/system/pdd-auth/info` - 查询授权信息 JSON
- `GET /api/v1/system/pdd-auth/page` - 授权信息查看页
- `POST /api/v1/system/pdd-logout` - 解绑授权

## 注意事项

- `pdd-cs-adapter` 必须已启动，默认端口 `8003`
- `.env` 必须配置 `PDD_USERNAME` 和 `PDD_PASSWORD`
- Playwright Chromium 必须已安装
- 后端运行环境必须能打开用户可见的浏览器窗口
- 如果服务跑在 Docker/Xvfb 内，浏览器可能只打开在容器虚拟显示中，用户桌面看不到
- 授权成功后的会话保存在后端 `PDD_DATA_DIR/pdd_storage_state.json`
- 建议持久化 `PDD_DATA_DIR`，避免容器重启后丢失 session

## 常见问题

### Q1: 浏览器启动失败

检查 Playwright Chromium 是否安装，并确认后端环境可以打开可见浏览器。

### Q2: 一直等待登录完成

确认用户是否已在打开的拼多多商家后台页面完成滑块、短信或扫码确认；如果登录窗口被关闭且未保存有效 Cookie，需要重新授权。

### Q3: 授权成功后无法使用自动化功能

检查 `/api/v1/system/pdd-auth/page`，确认会话文件存在且检测到有效登录 Cookie。
