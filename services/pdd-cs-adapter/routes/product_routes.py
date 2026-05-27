"""
商品管理API路由 - 拼多多客服适配器
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


class ProductResponse(BaseModel):
    """商品响应"""
    goods_id: int
    goods_name: str
    goods_thumbnail_url: Optional[str] = None
    goods_status: int = 0
    goods_sign: Optional[str] = None
    min_group_price: Optional[int] = None
    min_normal_price: Optional[int] = None
    cat_id: Optional[int] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None


class ProductListResponse(BaseModel):
    """商品列表响应"""
    total: int
    page: int
    page_size: int
    goods_list: List[Dict[str, Any]]


class SkuPriceUpdate(BaseModel):
    """SKU价格更新"""
    sku_id: int
    price: int  # 单位：分


class SkuStockUpdate(BaseModel):
    """SKU库存更新"""
    sku_id: int
    stock: int


class UpdatePriceRequest(BaseModel):
    """更新价格请求"""
    goods_id: int
    sku_prices: List[SkuPriceUpdate]


class UpdateStockRequest(BaseModel):
    """更新库存请求"""
    goods_id: int
    sku_stocks: List[SkuStockUpdate]


@router.get("/list", response_model=ProductListResponse)
async def get_product_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search_goods_name: Optional[str] = Query(None, description="商品名称搜索"),
    goods_status: Optional[int] = Query(None, description="商品状态 (1-上架, 2-下架, 3-售罄, 4-已删除)"),
):
    """获取商品列表
    
    通过拼多多开放平台API获取店铺商品列表，支持搜索和状态筛选。
    """
    try:
        result = await pdd_client.get_product_list(
            page=page,
            page_size=page_size,
            search_goods_name=search_goods_name,
            goods_status=goods_status,
        )
        
        response_key = "goods_detail_get_response"
        if response_key in result:
            data = result[response_key]
            return ProductListResponse(
                total=data.get("total_count", 0),
                page=page,
                page_size=page_size,
                goods_list=data.get("goods_detail_list", []),
            )
        
        # 直接返回结构
        return ProductListResponse(
            total=result.get("total_count", 0),
            page=page,
            page_size=page_size,
            goods_list=result.get("goods_list", []),
        )
        
    except Exception as e:
        logger.error(f"获取商品列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取商品列表失败: {str(e)}")


@router.get("/detail/{goods_id}")
async def get_product_detail(goods_id: int):
    """获取商品详情
    
    通过商品ID获取商品的详细信息，包括SKU、价格、库存等。
    """
    try:
        result = await pdd_client.get_product_detail(goods_id)
        return {
            "goods_id": goods_id,
            "data": result,
        }
    except Exception as e:
        logger.error(f"获取商品详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取商品详情失败: {str(e)}")


@router.put("/price")
async def update_product_price(request: UpdatePriceRequest):
    """更新商品价格
    
    批量更新商品SKU的价格。价格单位为分。
    """
    try:
        sku_prices = [
            {"sku_id": item.sku_id, "price": item.price}
            for item in request.sku_prices
        ]
        
        result = await pdd_client.update_product_price(
            goods_id=request.goods_id,
            sku_prices=sku_prices,
        )
        
        return {
            "message": "价格更新成功",
            "goods_id": request.goods_id,
            "updated_skus": len(request.sku_prices),
            "data": result,
        }
    except Exception as e:
        logger.error(f"更新商品价格失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新商品价格失败: {str(e)}")


@router.put("/stock")
async def update_product_stock(request: UpdateStockRequest):
    """更新商品库存
    
    批量更新商品SKU的库存数量。
    """
    try:
        sku_stocks = [
            {"sku_id": item.sku_id, "stock": item.stock}
            for item in request.sku_stocks
        ]
        
        result = await pdd_client.update_product_stock(
            goods_id=request.goods_id,
            sku_stocks=sku_stocks,
        )
        
        return {
            "message": "库存更新成功",
            "goods_id": request.goods_id,
            "updated_skus": len(request.sku_stocks),
            "data": result,
        }
    except Exception as e:
        logger.error(f"更新商品库存失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新商品库存失败: {str(e)}")
