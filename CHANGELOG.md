# Changelog

本文件记录 ecom-automation 项目的重要变更。
格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

---

## [Unreleased] - 开发中

### 待完成
- OMS 跨平台订单统一模型完善 (EC-005)
- 暗色模式支持 (EC-009)
- 统一日志收集和监控 (EC-012)
- CI/CD 流水线配置 (EC-013)

---

## [0.4.0] - 2026-05-29

### 文档完善
- 📖 更新 kuaishou-adapter README — 补充 token-status/force-refresh 端点、调度器说明
- 📖 更新 OMS 订单中台 README — 补全全部 API 端点（订单17个、库存18个、工单23个、看板7个）
- 📖 修复 README 端口不一致 + API 文档补充客户管理路由
- 📖 完善 API 文档 — OMS 60+ 接口、网关新增库存/工单/看板/设置路由
- 📖 完善 API 文档 — 补充 product-service 完整 CRUD、平台适配器、RAG 缓存管理

### 新功能
- ✨ Dashboard 真实数据 API 端点 (`/stats`、`/trend`)
- ✨ 客户管理接入真实 API（代理路由模式）

---

## [0.3.0] - 2026-05-28

### 新功能
- ✨ **Marketing 营销中心** — 优惠券/活动/分销/佣金全流程接入 API 层
- ✨ **Settings 页面** — 抖音对接 Tab 接入真实 API 存储
- ✨ **商品管理** — 完整 CRUD 后端 + 前端真实 API 对接
- ✨ **订单管理** — 前后端打通，替换模拟数据为真实 API 调用
- ✨ **API 网关代理层** — 统一路由转发到后端微服务，新增库存/工单路由
- ✨ **OAuth Token 自动刷新** — 后台定时检查、提前30分钟刷新、指数退避重试 (EC-004)
- ✨ **拼多多商品/订单 API** — 商品列表/详情/价格/库存、订单全流程管理
- ✨ **Dashboard 数据可视化增强** — 多指标趋势对比、热销 TOP6、转化漏斗、实时订单 Feed (EC-006)
- ✨ **客户管理批量操作** — 批量打标签/发消息/删除 + 客户分群面板
- ✨ **竞品分析升级 v4** — 趋势分析/批量操作/价格走势/强度排名
- ✨ **反爬虫策略完善** — 请求限速器、代理轮换、UA管理、指数退避重试、CAPTCHA 检测 (EC-011)
- ✨ **RAG 查询缓存优化** — 添加缓存统计与失效管理端点

### 修复
- 🐛 **统一错误处理** — 标准化错误响应、自定义异常体系、请求追踪中间件 (EC-003)
- 🐛 商品 CRUD 数据库 schema 不同步问题
- 🐛 Settings 页面 API 路径和响应格式修正
- 🐛 Docker Compose 补全全部 9 个微服务 + 健康检查 + 生产配置
- 🐛 前端 3 个页面 CSS 缺失导致渲染异常
- 🐛 统一 API 响应格式、错误处理、参数验证
- 🐛 OMS models/ 命名冲突，订单数据 SQLite 持久化

### 文档
- 📖 添加故障排除指南 `docs/TROUBLESHOOTING.md`
- 📖 添加开发指南 `docs/DEVELOPMENT.md`
- 📖 为 product-service 添加 README.md
- 📖 为 api-gateway 添加 README.md
- 📖 生成完整 API 文档和 OpenAPI 规范
- 📖 更新 BUG-TRACKING.md — 标记 6 个问题已修复

---

## [0.2.0] - 2026-05-27

### 新功能
- ✨ **Docker 部署体系** — docker-compose.yml + 生产环境配置 + Makefile 快捷命令
- ✨ **Dashboard 数据可视化** — 多维度图表、平台分组、环比对比 (EC-006 初版)
- ✨ **订单确认收货 + 导出** (EC-008 部分修复)
- ✨ **商品批量调价** (EC-007 部分修复)
- ✨ **客户分群分析** (EC-NEW-02)
- ✨ 路由配置补充 — Settings 和 Competitors 路由及菜单 (EC-002 部分修复)

### 文档
- 📖 初始化项目管理文件 — BUG-TRACKING.md + PROGRESS.md

---

## [0.1.0] - 2026-04-25

### 初始版本
- ✨ 10 个微服务骨架搭建完成
  - `api-gateway` (8000) — 统一 REST API 网关
  - `douyin-adapter` (8001) — 抖店平台适配器
  - `kuaishou-adapter` (8002) — 快手平台适配器
  - `pdd-cs-adapter` (8003) — 拼多多客服自动化
  - `xianyu-adapter` (8004) — 闲鱼自动化
  - `oms-service` (8005) — 订单中台
  - `product-service` (8006) — 商品与分类管理
  - `rag-service` (8009) — RAG 知识库检索
  - `hermes-control` (8080) — 总控、策略、调度、报表
  - `competitor-crawler` (8008) — 竞品数据采集与分析
- ✨ Admin 前端 12 个页面（Dashboard、Products、Orders、Customers、Marketing、Analytics、Competitors、CustomerService、Finance、SupplyChain、Settings、System）
- ✨ 统一鉴权层 + 多平台 SKU + 统一订单模型
- ✨ 数据库初始化脚本 + PostgreSQL + Redis
- ✨ Hermes Agent Skills 集成（竞品分析、选品评分、文案生成、客服路由、售后分诊、风险监控、日报）

---

## 版本说明

| 版本 | 日期 | 重点 |
|------|------|------|
| 0.1.0 | 2026-04-25 | 项目骨架 + 前端页面 |
| 0.2.0 | 2026-05-27 | Docker 部署 + 管理文档 |
| 0.3.0 | 2026-05-28 | 前后端联调 + 核心功能实现 |
| 0.4.0 | 2026-05-29 | API 文档完善 + 真实数据接入 |
