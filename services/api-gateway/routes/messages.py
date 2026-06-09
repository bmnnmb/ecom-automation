"""
客服消息路由

使用统一错误处理和标准化响应格式。
"""
from fastapi import APIRouter, Query, Path
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import random

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
# 种子数据生成
# ============================================================

def _generate_seed_conversations():
    """生成客服会话种子数据"""
    random.seed(42)
    now = datetime.now()

    conversations = []
    customers = [
        {"id": "CUST-001", "name": "王小明", "avatar": ""},
        {"id": "CUST-002", "name": "李美丽", "avatar": ""},
        {"id": "CUST-003", "name": "张大伟", "avatar": ""},
        {"id": "CUST-004", "name": "赵晓燕", "avatar": ""},
        {"id": "CUST-005", "name": "刘强", "avatar": ""},
        {"id": "CUST-006", "name": "陈芳", "avatar": ""},
        {"id": "CUST-007", "name": "杨洋", "avatar": ""},
        {"id": "CUST-008", "name": "黄丽", "avatar": ""},
        {"id": "CUST-009", "name": "周杰", "avatar": ""},
        {"id": "CUST-010", "name": "吴敏", "avatar": ""},
    ]

    platforms = ['douyin', 'pdd', 'xianyu', 'kuaishou']

    chat_templates = [
        [
            {"role": "customer", "content": "你好，我想问一下这个蓝牙耳机的续航时间是多久？"},
            {"role": "agent", "content": "您好！这款蓝牙耳机的续航时间约为8小时，配合充电仓可达32小时。请问还有其他问题吗？"},
            {"role": "customer", "content": "好的，那支持快充吗？"},
            {"role": "agent", "content": "支持的，充电15分钟可使用2小时。"},
        ],
        [
            {"role": "customer", "content": "我的订单什么时候能发货？"},
            {"role": "agent", "content": "您好，请问您的订单号是多少？我帮您查询一下。"},
            {"role": "customer", "content": "ORD-20260528001"},
            {"role": "agent", "content": "已查到，您的订单预计明天发出，后天可到。"},
        ],
        [
            {"role": "customer", "content": "这个商品可以退货吗？"},
            {"role": "agent", "content": "可以的，7天无理由退换货。请问是什么原因想退货呢？"},
            {"role": "customer", "content": "颜色和图片不太一样"},
            {"role": "agent", "content": "非常抱歉给您带来不好的体验，我们可以为您办理换货或退款，您看哪种方式更方便？"},
        ],
        [
            {"role": "customer", "content": "有没有优惠券可以用？"},
            {"role": "agent", "content": "有的！现在有满100减20的新人专享券，您领取了吗？"},
            {"role": "customer", "content": "在哪里领？"},
            {"role": "agent", "content": "在首页banner点击即可领取，或者我直接发给您链接。"},
        ],
        [
            {"role": "customer", "content": "充电宝能带上飞机吗？"},
            {"role": "agent", "content": "20000mAh的充电宝是可以带上飞机的，符合民航规定（不超过27000mAh）。"},
            {"role": "customer", "content": "好的谢谢"},
            {"role": "agent", "content": "不客气，祝您旅途愉快！"},
        ],
    ]

    for i, cust in enumerate(customers):
        msgs = chat_templates[i % len(chat_templates)]
        messages = []
        for j, msg in enumerate(msgs):
            msg_time = now - timedelta(minutes=(len(msgs) - j) * 5 + random.randint(0, 60))
            messages.append({
                "id": f"MSG-{i*10+j+1:06d}",
                "conversationId": f"CONV-{i+1:04d}",
                "senderId": cust["id"] if msg["role"] == "customer" else "AGENT-001",
                "senderName": cust["name"] if msg["role"] == "customer" else "客服小美",
                "senderType": msg["role"],
                "content": msg["content"],
                "messageType": "text",
                "createdAt": msg_time.isoformat(),
            })

        last_msg = messages[-1] if messages else None
        conversations.append({
            "id": f"CONV-{i+1:04d}",
            "customerId": cust["id"],
            "customerName": cust["name"],
            "customerAvatar": cust["avatar"],
            "platform": platforms[i % len(platforms)],
            "lastMessage": last_msg["content"] if last_msg else "",
            "lastMessageTime": last_msg["createdAt"] if last_msg else now.isoformat(),
            "unreadCount": random.randint(0, 3),
            "status": random.choice(["active", "active", "pending", "resolved"]),
            "messages": messages,
            "createdAt": (now - timedelta(days=random.randint(1, 30))).isoformat(),
        })

    random.seed()
    return conversations


# ============================================================
# 数据存储
# ============================================================
_conversations = _generate_seed_conversations()
_messages_db: dict = {}
_message_counter = 100


def _next_message_id() -> str:
    global _message_counter
    _message_counter += 1
    return f"MSG-{_message_counter:06d}"


# ============================================================
# 会话路由 (必须在 /{message_id} 之前定义)
# ============================================================

@router.get("/conversations")
async def list_conversations(
    platform: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取客服会话列表"""
    items = _conversations.copy()
    if platform:
        items = [c for c in items if c['platform'] == platform]
    if status:
        items = [c for c in items if c['status'] == status]
    if keyword:
        kw = keyword.lower()
        items = [c for c in items if kw in c['customerName'].lower() or kw in c.get('lastMessage', '').lower()]

    total = len(items)
    start = (page - 1) * page_size
    paged = items[start:start + page_size]
    return success_response(data={"items": paged, "total": total})


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """获取会话详情（含消息列表）"""
    conv = next((c for c in _conversations if c['id'] == conversation_id), None)
    if not conv:
        return success_response(data=None, message="会话不存在")

    conv['unreadCount'] = 0
    return success_response(data=conv)


@router.post("/conversations/{conversation_id}/send")
async def send_message_to_conversation(conversation_id: str, body: MessageReply):
    """向会话发送消息"""
    conv = next((c for c in _conversations if c['id'] == conversation_id), None)
    if not conv:
        return success_response(data=None, message="会话不存在")

    now = datetime.now().isoformat()
    new_msg = {
        "id": _next_message_id(),
        "conversationId": conversation_id,
        "senderId": "AGENT-001",
        "senderName": "客服小美",
        "senderType": "agent",
        "content": body.content,
        "messageType": body.message_type,
        "createdAt": now,
    }

    conv['messages'].append(new_msg)
    conv['lastMessage'] = body.content
    conv['lastMessageTime'] = now

    return success_response(data=new_msg, message="消息已发送")


@router.get("/stats")
async def get_message_stats():
    """获取客服消息统计"""
    total_conversations = len(_conversations)
    active = sum(1 for c in _conversations if c['status'] == 'active')
    pending = sum(1 for c in _conversations if c['status'] == 'pending')
    total_unread = sum(c['unreadCount'] for c in _conversations)

    return success_response(data={
        "totalConversations": total_conversations,
        "activeConversations": active,
        "pendingConversations": pending,
        "unreadMessages": total_unread,
    })


# ============================================================
# 消息路由 (在会话路由之后)
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
    paged = items[start: start + page_size]

    return paginated_response(items=paged, total=total, page=page, page_size=page_size)


@router.post("/")
async def create_message(message: MessageCreate):
    """创建客服消息"""
    if message.message_type not in VALID_MESSAGE_TYPES:
        return success_response(data=None, message=f"无效的消息类型: {message.message_type}")

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
        return success_response(data=None, message="消息不存在")
    return success_response(data=msg)


@router.post("/{message_id}/reply")
async def reply_message(
    message_id: str = Path(..., description="消息ID"),
    body: MessageReply = ...,
):
    """回复客服消息"""
    msg = _messages_db.get(message_id)
    if not msg:
        return success_response(data=None, message="消息不存在")

    reply_id = _next_message_id()
    now = datetime.now().isoformat()

    reply_record = {
        "id": reply_id,
        "shop_id": msg.get("shop_id", ""),
        "platform": msg.get("platform", ""),
        "customer_id": msg.get("customer_id", ""),
        "content": body.content,
        "message_type": body.message_type,
        "direction": "outgoing",
        "status": "sent",
        "reply_to": message_id,
        "created_at": now,
    }
    _messages_db[reply_id] = reply_record

    msg["status"] = "replied"

    return success_response(data=reply_record, message="回复已发送")
