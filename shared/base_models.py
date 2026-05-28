"""
共享数据模型基类
统一各服务的模型规范，提供通用混入类和工具函数
"""
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, event
from sqlalchemy.orm import declarative_base, declared_attr


class CustomBase:
    """自定义基类 - 提供通用功能"""

    @declared_attr
    def __tablename__(cls):
        """自动生成表名"""
        return cls.__name__.lower() + 's'

    id = Column(Integer, primary_key=True, autoincrement=True)

    def to_dict(self) -> Dict[str, Any]:
        """将模型转换为字典"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif hasattr(value, 'value'):  # Enum类型
                value = value.value
            result[column.name] = value
        return result

    def update(self, **kwargs):
        """更新模型属性"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


Base = declarative_base(cls=CustomBase)


class TimestampMixin:
    """时间戳混入类"""
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")


class SoftDeleteMixin:
    """软删除混入类"""
    is_deleted = Column(Boolean, default=False, nullable=False, index=True, comment="是否已删除")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")

    def soft_delete(self):
        """执行软删除"""
        self.is_deleted = True
        self.deleted_at = datetime.now()

    def restore(self):
        """恢复软删除"""
        self.is_deleted = False
        self.deleted_at = None


class AuditMixin:
    """审计混入类"""
    created_by = Column(String(50), nullable=True, comment="创建人")
    updated_by = Column(String(50), nullable=True, comment="更新人")


class StatusMixin:
    """状态混入类"""
    status = Column(String(20), default="active", nullable=False, comment="状态")
    status_changed_at = Column(DateTime, nullable=True, comment="状态变更时间")

    def change_status(self, new_status: str, user: Optional[str] = None):
        """变更状态"""
        self.status = new_status
        self.status_changed_at = datetime.now()
        if hasattr(self, 'updated_by') and user:
            self.updated_by = user


def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """序列化日期时间"""
    return dt.isoformat() if dt else None


def generate_id(prefix: str, num: int, width: int = 6) -> str:
    """生成格式化ID"""
    return f"{prefix}{str(num).zfill(width)}"
