"""
竞品分析路由

提供竞品监控数据的 CRUD 接口。
使用内存存储 + 种子数据，前端可直接对接。
"""
from fastapi import APIRouter, Query, Path
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import random

from utils.responses import success_response, paginated_response

router = APIRouter()


# ============================================================
# 请求/响应模型
# ============================================================

class CompetitorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="竞品名称")
    platform: str = Field(..., description="平台")
    competitor: Optional[str] = Field(None, description="竞品店铺")
    theirPrice: float = Field(..., gt=0, description="竞品价格")
    ourPrice: float = Field(..., gt=0, description="我方价格")
    theirSales: Optional[int] = Field(0, description="竞品销量")
    ourSales: Optional[int] = Field(0, description="我方销量")
    theirRating: Optional[float] = Field(4.5, description="竞品评分")


class PriceAdjust(BaseModel):
    ourPrice: float = Field(..., gt=0, description="新价格")
    reason: Optional[str] = Field(None, description="调价原因")


# ============================================================
# 种子数据生成
# ============================================================

PRODUCT_NAMES = [
    '智能降噪蓝牙耳机 Pro Max', '便携式迷你投影仪 4K高清', '磁吸无线充电宝 20000mAh',
    '超轻碳纤维行李箱 20寸', '人体工学护腰办公椅', '智能恒温保温杯 500ml',
    '空气净化器 HEPA滤网', '电动牙刷 声波震动款', '智能手表 运动健康监测',
    '降噪头戴式耳机 Hi-Res', '机械键盘 青轴RGB背光', 'USB-C扩展坞 12合1',
    '桌面加湿器 超声波静音', '智能门锁 指纹密码锁', '无线鼠标 人体工学设计',
    '颈椎按摩仪 热敷理疗', 'LED护眼台灯 无极调光', '筋膜枪 深层肌肉放松',
    '扫地机器人 激光导航', '智能音箱 语音助手',
]

SHOPS = [
    '数码旗舰店', '科技优品馆', '智能生活馆', '品质电子城', '潮流数码坊',
    '好物精选店', '电子先锋馆', '智享家居店', '创新科技馆', '优选数码城',
]

PLATFORMS = ['douyin', 'pdd', 'xianyu', 'kuaishou']


def _generate_seed_data():
    """生成 20 条竞品种子数据"""
    items = []
    random.seed(42)  # 固定种子，保证每次启动数据一致
    for i in range(20):
        base_price = random.uniform(50, 800)
        diff_pct = random.uniform(-15, 25)
        their_price = round(base_price, 2)
        our_price = round(base_price * (1 + diff_pct / 100), 2)
        items.append({
            "id": f"COMP-{i+1:04d}",
            "name": PRODUCT_NAMES[i % len(PRODUCT_NAMES)],
            "platform": PLATFORMS[i % len(PLATFORMS)],
            "competitor": SHOPS[i % len(SHOPS)],
            "theirPrice": their_price,
            "ourPrice": our_price,
            "priceDiff": round((our_price - their_price) / their_price * 100, 1),
            "theirSales": random.randint(100, 8000),
            "ourSales": random.randint(50, 5000),
            "theirRating": round(random.uniform(4.0, 5.0), 1),
            "status": "active",
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 60))).isoformat(),
            "updated_at": datetime.now().isoformat(),
        })
    random.seed()  # 恢复随机种子
    return items


# 内存数据存储
_competitors_db: dict = {}
_competitor_counter = 20


def _init_seed_data():
    """初始化种子数据"""
    global _competitors_db
    seeds = _generate_seed_data()
    for item in seeds:
        _competitors_db[item["id"]] = item


_init_seed_data()


def _next_competitor_id() -> str:
    global _competitor_counter
    _competitor_counter += 1
    return f"COMP-{_competitor_counter:04d}"


# ============================================================
# 路由
# ============================================================

@router.get("/")
async def list_competitors(
    platform: Optional[str] = Query(None, description="按平台筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
):
    """获取竞品列表"""
    items = list(_competitors_db.values())

    if platform and platform != 'all':
        items = [c for c in items if c["platform"] == platform]
    if keyword:
        kw = keyword.lower()
        items = [c for c in items if kw in c["name"].lower() or kw in c.get("competitor", "").lower()]

    total = len(items)
    start = (page - 1) * page_size
    paged = items[start: start + page_size]

    return {"success": True, "data": {"items": paged, "total": total}}


@router.post("/")
async def create_competitor(competitor: CompetitorCreate):
    """添加竞品监控"""
    comp_id = _next_competitor_id()
    now = datetime.now().isoformat()

    price_diff = round((competitor.ourPrice - competitor.theirPrice) / competitor.theirPrice * 100, 1)

    record = {
        "id": comp_id,
        "name": competitor.name,
        "platform": competitor.platform,
        "competitor": competitor.competitor or "未知店铺",
        "theirPrice": competitor.theirPrice,
        "ourPrice": competitor.ourPrice,
        "priceDiff": price_diff,
        "theirSales": competitor.theirSales or 0,
        "ourSales": competitor.ourSales or 0,
        "theirRating": competitor.theirRating or 4.5,
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
        return success_response(data=None, message="竞品不存在")
    return success_response(data=comp)


@router.patch("/{competitor_id}")
async def update_competitor(competitor_id: str, adjust: PriceAdjust):
    """调整竞品价格"""
    comp = _competitors_db.get(competitor_id)
    if not comp:
        return success_response(data=None, message="竞品不存在")

    old_price = comp["ourPrice"]
    comp["ourPrice"] = adjust.ourPrice
    comp["priceDiff"] = round((adjust.ourPrice - comp["theirPrice"]) / comp["theirPrice"] * 100, 1)
    comp["updated_at"] = datetime.now().isoformat()

    return success_response(data=comp, message=f"价格已从 ¥{old_price:.2f} 调整为 ¥{adjust.ourPrice:.2f}")


@router.delete("/{competitor_id}")
async def delete_competitor(competitor_id: str = Path(..., description="竞品ID")):
    """删除竞品监控"""
    comp = _competitors_db.pop(competitor_id, None)
    if not comp:
        return success_response(data=None, message="竞品不存在")
    return success_response(message=f"竞品 {competitor_id} 已删除")


@router.get("/stats/summary")
async def get_competitor_stats():
    """获取竞品统计概览"""
    items = list(_competitors_db.values())
    total = len(items)
    if total == 0:
        return success_response(data={"total": 0, "avgDiff": 0, "cheaperCount": 0, "expensiveCount": 0})

    avg_diff = sum(c["priceDiff"] for c in items) / total
    cheaper = sum(1 for c in items if c["priceDiff"] < 0)
    expensive = sum(1 for c in items if c["priceDiff"] > 0)

    return success_response(data={
        "total": total,
        "avgDiff": round(avg_diff, 1),
        "cheaperCount": cheaper,
        "expensiveCount": expensive,
    })
