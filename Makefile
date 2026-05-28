# ============================================
# Hermes 电商自动化系统 - Makefile
# ============================================
# 常用操作快捷命令
# 使用: make [target]
# ============================================

.PHONY: help build up down restart logs ps health clean backup restore

# 默认目标
help: ## 显示帮助信息
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─── 生命周期 ───

build: ## 构建所有服务镜像
	docker compose build

build-no-cache: ## 强制重建所有镜像（无缓存）
	docker compose build --no-cache

build-svc: ## 构建指定服务 (用法: make build-svc SVC=api-gateway)
	docker compose build $(SVC)

up: ## 启动所有服务
	docker compose up -d

up-infra: ## 仅启动基础设施 (postgres + redis)
	docker compose up -d postgres redis

down: ## 停止所有服务
	docker compose down

down-volumes: ## 停止所有服务并删除数据卷 (⚠️ 数据丢失)
	docker compose down -v

restart: ## 重启所有服务
	docker compose restart

restart-svc: ## 重启指定服务 (用法: make restart-svc SVC=api-gateway)
	docker compose restart $(SVC)

# ─── 监控 ───

ps: ## 查看服务状态
	docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

logs: ## 查看所有服务日志（实时）
	docker compose logs -f

logs-svc: ## 查看指定服务日志 (用法: make logs-svc SVC=api-gateway)
	docker compose logs -f $(SVC)

logs-tail: ## 查看最后 100 行日志
	docker compose logs --tail=100

health: ## 检查所有服务健康状态
	@echo "=== 服务健康状态 ==="
	@docker inspect --format='{{.Name}}: {{.State.Health.Status}}' $$(docker compose ps -q) 2>/dev/null | sed 's|/||' || echo "无运行中的容器"

stats: ## 查看容器资源使用
	docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# ─── 数据库 ───

db-shell: ## 进入 PostgreSQL shell
	docker compose exec postgres psql -U ecom -d ecom_automation

db-migrate: ## 执行数据库迁移
	docker compose exec -T postgres psql -U ecom -d ecom_automation < database/migrations/001_phase1_init.sql

backup: ## 备份数据库
	@mkdir -p backups
	docker compose exec postgres pg_dump -U ecom ecom_automation > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "备份完成: backups/backup_$$(date +%Y%m%d_%H%M%S).sql"

restore: ## 恢复数据库 (用法: make restore FILE=backup.sql)
	cat $(FILE) | docker compose exec -T postgres psql -U ecom -d ecom_automation

# ─── Redis ───

redis-shell: ## 进入 Redis CLI
	docker compose exec redis redis-cli

redis-dbsize: ## 查看各 Redis DB 大小
	@for db in 0 1 2 3 4 5 6 7 8; do \
		echo -n "DB $$db: "; \
		docker compose exec redis redis-cli -n $$db DBSIZE; \
	done

# ─── 调试 ───

shell: ## 进入容器 shell (用法: make shell SVC=api-gateway)
	docker compose exec $(SVC) bash

# ─── 清理 ───

clean: ## 清理停止的容器和未使用的镜像
	docker container prune -f
	docker image prune -f

clean-all: ## 清理所有未使用的资源 (⚠️ 谨慎使用)
	docker system prune -af --volumes

# ─── 生产部署 ───

prod-up: ## 生产环境启动 (带资源限制)
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-build: ## 生产环境构建并启动
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

prod-down: ## 生产环境停止
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down
