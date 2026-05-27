"""
竞品分析路由

使用统一错误处理和标准化响应格式。
"""
from fastapi import APIRouter, Query, Path
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

from utils.errors import NotFoundError, ValidationError
from utils.responses import success_response, paginated_response

router = APIRouter()


# ============================================================
# 请求/响应模型
# ============================================================

class CompetitorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="竞品名称")
    platform: str = Field(..., description="平台")
    shop_url: Optional[str] = Field(None, description="竞品店铺链接")
    category: Optional[str] = Field(None, description="品类")
    notes: Optional[str] = Field(None, max_length=1000, description="备注")


# ============================================================
# 模拟数据存储
# ============================================================
_competitors_db: dict = {}
_competitor_counter = 0


def _next_competitor_id() -> str:
    global _competitor_counter
    _competitor_counter += 1
    return f"COMP-{_competitor_counter:06d}"


# ============================================================
# 路由
# ============================================================

@router.get("/")
async def list_competitors(
    platform: Optional[str] = Query(None, description="按平台筛选"),
    category: Optional[str] = Query(None, description="按品类筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """获取竞品列表"""
    items = list(_competitors_db.values())

    if platform:
        items = [c for c in items if c["platform"] == platform]
    if category:
        items = [c for c in items if c.get("category") == category]
    if keyword:
        kw = keyword.lower()
        items = [c for c in items if kw in c["name"].lower()]

    total = len(items)
    start = (page - 1) * page_size
    paged = items[start : start + page_size]

    return paginated_response(items=paged, total=total, page=page, page_size=page_size)


@router.post("/")
async def create_competitor(competitor: CompetitorCreate):
    """添加竞品监控"""
    comp_id = _next_competitor_id()
    now = datetime.now().isoformat()

    record = {
        "id": comp_id,
        "name": competitor.name,
        "platform": competitor.platform,
        "shop_url": competitor.shop_url,
        "category": competitor.category,
        "notes": competitor.notes,
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }
    _competitors_db[comp_id] = record

    return success_response(data=record, message="竞品监控已添加")


@router.get("/{competitor_id}")
async def get_competitor(competitor_id: str = Path(..., description="竞品ID")):
    """获取竞品详情"""
    comp = _competitors_db.get(competitor_id)
    if not comp:
        raise NotFoundError(resource="竞品", resource_id=competitor_id)
    return success_response(data=comp)


@router.delete("/{competitor_id}")
async def delete_competitor(competitor_id: str = Path(..., description="竞品ID")):
    """删除竞品监控"""
    comp = _competitors_db.get(competitor_id)
    if not comp:
        raise NotFoundError(resource="竞品", resource_id=competitor_id)

    del _competitors_db[competitor_id]
    return success_response(message=f"竞品 {competitor_id} 已删除")
