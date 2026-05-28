"""
OMS 数据库配置
支持 PostgreSQL (生产) 和 SQLite (本地开发) 两种后端。
优先使用环境变量 DATABASE_URL，未设置时默认 SQLite。
"""
import os
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime,
    JSON, create_engine, event
)
from sqlalchemy.orm import declarative_base, sessionmaker

# ─── 数据库 URL ────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL or DATABASE_URL.startswith("postgresql"):
    # 本地开发: 使用 SQLite，零依赖
    _db_path = os.path.join(os.path.dirname(__file__), "data", "oms.db")
    os.makedirs(os.path.dirname(_db_path), exist_ok=True)
    DATABASE_URL = f"sqlite:///{_db_path}"
    USE_SQLITE = True
else:
    USE_SQLITE = False

# ─── 引擎 & 会话 ───────────────────────────────────────────
engine = create_engine(DATABASE_URL, echo=False)

# SQLite 外键支持
if USE_SQLITE:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()


def get_db():
    """获取数据库会话 (同步)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """创建所有表"""
    # 导入模型确保它们已注册到 Base
    import order_db_models  # noqa: F401
    Base.metadata.create_all(bind=engine)
