"""
客服消息路由

使用统一错误处理和标准化响应格式。
"""
from fastapi import APIRouter, Query, Path
from typing import Optional
from pydantic import BaseModel, Field

from utils.errors import NotFoundError, ValidationError
from utils.responses import success_response, paginated_response

router = APIRouter()


# ============================================================
# 请求/响应模型
# ============================================================

class MessageCreate(BaseModel):
    shop_id: str = Field(..., description="店铺ID")
    platform: str = Field(..., description="来源平台")
    customer_id: str = Field(..., description="客户ID")
    content: str = Field(..., min_length=1, max_length=5000, description="消息内容")
    message_type: str = Field("text", description="消息类型: text | image | video")


class MessageReply(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000, description="回复内容")
    message_type: str = Field("text", description="消息类型: text | image | video")


VALID_MESSAGE_TYPES = {"text", "image", "video", "file", "link"}


# ============================================================
# 模拟数据存储
# ============================================================
_messages_db: dict = {}
_message_counter = 0


def _next_message_id() -> str:
    global _message_counter
    _message_counter += 1
    return f"MSG-{_message_counter:06d}"


# ============================================================
# 路由
# ============================================================

@router.get("/")
async def list_messages(
    shop_id: Optional[str] = Query(None, description="按店铺筛选"),
    platform: Optional[str] = Query(None, description="按平台筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """获取客服消息列表"""
    items = list(_messages_db.values())

    if shop_id:
        items = [m for m in items if m["shop_id"] == shop_id]
    if platform:
        items = [m for m in items if m["platform"] == platform]
    if keyword:
        kw = keyword.lower()
        items = [m for m in items if kw in m["content"].lower()]

    total = len(items)
    start = (page - 1) * page_size
    paged = items[start : start + page_size]

    return paginated_response(items=paged, total=total, page=page, page_size=page_size)


@router.post("/")
async def create_message(message: MessageCreate):
    """创建客服消息"""
    if message.message_type not in VALID_MESSAGE_TYPES:
        raise ValidationError(
            message=f"无效的消息类型: {message.message_type}",
            detail=f"支持的类型: {', '.join(VALID_MESSAGE_TYPES)}",
        )

    from datetime import datetime
    msg_id = _next_message_id()
    now = datetime.now().isoformat()

    record = {
        "id": msg_id,
        "shop_id": message.shop_id,
        "platform": message.platform,
        "customer_id": message.customer_id,
        "content": message.content,
        "message_type": message.message_type,
        "direction": "incoming",
        "status": "unread",
        "created_at": now,
    }
    _messages_db[msg_id] = record

    return success_response(data=record, message="消息已记录")


@router.get("/{message_id}")
async def get_message(message_id: str = Path(..., description="消息ID")):
    """获取消息详情"""
    msg = _messages_db.get(message_id)
    if not msg:
        raise NotFoundError(resource="消息", resource_id=message_id)
    return success_response(data=msg)


@router.post("/{message_id}/reply")
async def reply_message(
    message_id: str = Path(..., description="消息ID"),
    body: MessageReply = ...,
):
    """回复客服消息"""
    msg = _messages_db.get(message_id)
    if not msg:
        raise NotFoundError(resource="消息", resource_id=message_id)

    if body.message_type not in VALID_MESSAGE_TYPES:
        raise ValidationError(
            message=f"无效的消息类型: {body.message_type}",
            detail=f"支持的类型: {', '.join(VALID_MESSAGE_TYPES)}",
        )

    from datetime import datetime
    reply_id = _next_message_id()
    now = datetime.now().isoformat()

    reply_record = {
        "id": reply_id,
        "shop_id": msg["shop_id"],
        "platform": msg["platform"],
        "customer_id": msg["customer_id"],
        "content": body.content,
        "message_type": body.message_type,
        "direction": "outgoing",
        "status": "sent",
        "reply_to": message_id,
        "created_at": now,
    }
    _messages_db[reply_id] = reply_record

    # 标记原消息为已回复
    msg["status"] = "replied"

    return success_response(data=reply_record, message="回复已发送")
