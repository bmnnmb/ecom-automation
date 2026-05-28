"""
Settings 系统设置路由

提供 /api/settings 的 GET/PUT 端点，
前端 Settings 页面通过这两个接口读取和保存系统配置。

数据持久化: 使用 JSON 文件存储在 data/settings.json
后续可替换为数据库存储。
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
from pathlib import Path
import json

from utils.responses import success_response

router = APIRouter()

# 数据文件路径
DATA_DIR = Path(__file__).parent.parent / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"

# 默认配置
DEFAULT_SETTINGS = {
    "general": {
        "shopName": "我的电商店铺",
        "logo": "",
        "contactPhone": "400-000-0000",
        "contactEmail": "support@example.com",
        "autoReply": True,
        "language": "zh-CN",
    },
    "platforms": {
        "douyin": {"enabled": True, "appId": "1903132504", "autoSync": True, "syncInterval": 15},
        "pdd": {"enabled": True, "appId": "", "autoSync": False, "syncInterval": 30},
        "xianyu": {"enabled": False, "appId": "", "autoSync": False, "syncInterval": 60},
        "kuaishou": {"enabled": False, "appId": "", "autoSync": False, "syncInterval": 30},
    },
    "notifications": {
        "orderAlert": True,
        "refundAlert": True,
        "stockAlert": True,
        "competitorAlert": True,
        "dailyReport": True,
        "alertChannel": "feishu",
    },
    "ai": {
        "autoCustomerService": True,
        "autoProductDescription": False,
        "autoPricing": False,
        "confidenceThreshold": 0.8,
        "model": "gpt-4",
    },
}


def _load_settings() -> dict:
    """从文件加载配置，不存在则返回默认值"""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            # 合并: 以默认值为基底，用保存的值覆盖（保证新增字段有默认值）
            merged = _deep_merge(DEFAULT_SETTINGS, saved)
            return merged
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_SETTINGS.copy()


def _save_settings(settings: dict) -> None:
    """保存配置到文件"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def _deep_merge(base: dict, override: dict) -> dict:
    """深度合并字典，override 中的值覆盖 base"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class SettingsUpdate(BaseModel):
    """设置更新请求体"""
    general: Optional[Dict[str, Any]] = None
    platforms: Optional[Dict[str, Any]] = None
    notifications: Optional[Dict[str, Any]] = None
    ai: Optional[Dict[str, Any]] = None


@router.get("")
async def get_settings():
    """
    获取系统配置

    返回当前系统全部配置信息，包括:
    - general: 基础设置 (店铺名称、联系方式等)
    - platforms: 平台配置 (各电商平台的开关和参数)
    - notifications: 通知设置
    - ai: AI功能配置
    """
    settings = _load_settings()
    return success_response(data=settings)


@router.put("")
async def update_settings(body: SettingsUpdate):
    """
    更新系统配置

    接受部分更新，只修改传入的 section，未传入的 section 保持不变。
    请求体示例:
    {
        "general": {"shopName": "新店铺名"},
        "notifications": {"orderAlert": false}
    }
    """
    current = _load_settings()

    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        return success_response(data=current, message="无变更")

    # 深度合并更新
    updated = _deep_merge(current, update_data)
    _save_settings(updated)

    return success_response(data=updated, message="设置已保存")
