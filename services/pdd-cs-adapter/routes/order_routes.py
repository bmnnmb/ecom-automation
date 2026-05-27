"""
订单管理API路由 - 拼多多客服适配器
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging

try:
    from ..pdd_client import pdd_client
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from pdd_client import pdd_client

logger = logging.getLogger(__name__)

router = APIRouter()


class OrderListResponse(BaseModel):
    """订单列表响应"""
    total: int
    page: int
    page_size: int
    order_list: List[Dict[str, Any]]


class ShipOrderRequest(BaseModel):
    """发货请求"""
    order_sn: str = Field(..., description="订单编号")
    logistics_id: int = Field(..., description="物流公司ID")
    tracking_number: str = Field(..., description="物流单号")


class RefundListResponse(BaseModel):
    """退款列表响应"""
    total: int
    page: int
    page_size: int
    refund_list: List[Dict[str, Any]]


@router.get("/list", response_model=OrderListResponse)
async def get_order_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    start_time: Optional[int] = Query(None, description="下单开始时间(时间戳)"),
    end_time: Optional[int] = Query(None, description="下单结束时间(时间戳)"),
    order_status: Optional[int] = Query(None, description="订单状态 (1-待发货, 2-已发货, 3-已签收, 5-已取消)"),
):
    """获取订单列表
    
    通过拼多多开放平台API获取店铺订单列表，支持时间范围和状态筛选。
    """
    try:
        result = await pdd_client.get_order_list(
            page=page,
            page_size=page_size,
            start_time=start_time,
            end_time=end_time,
            order_status=order_status,
        )
        
        response_key = "order_list_get_response"
        if response_key in result:
            data = result[response_key]
            return OrderListResponse(
                total=data.get("total_count", 0),
                page=page,
                page_size=page_size,
                order_list=data.get("order_list", []),
            )
        
        return OrderListResponse(
            total=result.get("total_count", 0),
            page=page,
            page_size=page_size,
            order_list=result.get("order_list", []),
        )
        
    except Exception as e:
        logger.error(f"获取订单列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取订单列表失败: {str(e)}")


@router.get("/detail/{order_sn}")
async def get_order_detail(order_sn: str):
    """获取订单详情
    
    通过订单编号获取订单的详细信息。
    """
    try:
        result = await pdd_client.get_order_detail(order_sn)
        return {
            "order_sn": order_sn,
            "data": result,
        }
    except Exception as e:
        logger.error(f"获取订单详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取订单详情失败: {str(e)}")


@router.post("/ship")
async def ship_order(request: ShipOrderRequest):
    """发货
    
    对已付款订单进行发货操作，需提供物流公司和运单号。
    
    常用物流公司ID：
    - 1: 邮政快递包裹
    - 2: 顺丰速运
    - 3: 圆通速递
    - 4: 中通快递
    - 5: 韵达快递
    - 6: 百世快递
    - 7: 申通快递
    - 8: 德邦快递
    - 9: 极兔速递
    """
    try:
        result = await pdd_client.ship_order(
            order_sn=request.order_sn,
            logistics_id=request.logistics_id,
            tracking_number=request.tracking_number,
        )
        
        return {
            "message": "发货成功",
            "order_sn": request.order_sn,
            "logistics_id": request.logistics_id,
            "tracking_number": request.tracking_number,
            "data": result,
        }
    except Exception as e:
        logger.error(f"发货失败: {e}")
        raise HTTPException(status_code=500, detail=f"发货失败: {str(e)}")


@router.get("/logistics/{order_sn}")
async def get_order_logistics(order_sn: str):
    """获取订单物流信息
    
    查询订单的物流跟踪信息。
    """
    try:
        result = await pdd_client.get_logistics_info(order_sn)
        return {
            "order_sn": order_sn,
            "data": result,
        }
    except Exception as e:
        logger.error(f"获取物流信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取物流信息失败: {str(e)}")


# ==================== 退款管理 ====================

@router.get("/refunds", response_model=RefundListResponse)
async def get_refund_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """获取退款列表
    
    获取店铺的退款/售后申请列表。
    """
    try:
        result = await pdd_client.get_refund_list(
            page=page,
            page_size=page_size,
        )
        
        response_key = "refund_list_increment_get_response"
        if response_key in result:
            data = result[response_key]
            return RefundListResponse(
                total=data.get("total_count", 0),
                page=page,
                page_size=page_size,
                refund_list=data.get("refund_list", []),
            )
        
        return RefundListResponse(
            total=result.get("total_count", 0),
            page=page,
            page_size=page_size,
            refund_list=result.get("refund_list", []),
        )
        
    except Exception as e:
        logger.error(f"获取退款列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取退款列表失败: {str(e)}")


@router.post("/refunds/{refund_id}/agree")
async def agree_refund(refund_id: int):
    """同意退款
    
    同意买家的退款申请。谨慎操作，此操作不可撤回。
    """
    try:
        result = await pdd_client.agree_refund(refund_id)
        return {
            "message": "已同意退款",
            "refund_id": refund_id,
            "data": result,
        }
    except Exception as e:
        logger.error(f"同意退款失败: {e}")
        raise HTTPException(status_code=500, detail=f"同意退款失败: {str(e)}")
