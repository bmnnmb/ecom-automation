"""
拼多多API客户端
基于拼多多开放平台API封装
"""
import time
import hashlib
import json
import logging
from typing import Dict, Any, Optional
import httpx

# 导入配置
try:
    from .config import settings
except ImportError:
    # 当直接运行时
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from config import settings

logger = logging.getLogger(__name__)


class PDDClient:
    """拼多多开放平台API客户端"""
    
    def __init__(self):
        self.client_id = settings.PDD_CLIENT_ID
        self.client_secret = settings.PDD_CLIENT_SECRET
        self.access_token = settings.PDD_ACCESS_TOKEN
        self.base_url = settings.PDD_API_BASE_URL
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def _generate_sign(self, params: Dict[str, Any]) -> str:
        """生成API签名"""
        # 拼多多签名算法：将参数按key排序后拼接，加上client_secret，进行MD5
        sorted_params = sorted(params.items())
        sign_str = self.client_secret
        for key, value in sorted_params:
            sign_str += f"{key}{value}"
        sign_str += self.client_secret
        
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()
    
    async def _request(self, method_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """通用API请求方法"""
        if params is None:
            params = {}
        
        # 基础参数
        base_params = {
            "type": method_name,
            "client_id": self.client_id,
            "timestamp": str(int(time.time())),
            "data_type": "JSON",
            "version": "1.0"
        }
        
        # 合并参数
        request_params = {**base_params, **params}
        
        # 生成签名
        sign = self._generate_sign(request_params)
        request_params["sign"] = sign
        
        try:
            response = await self.client.post(
                self.base_url,
                data=request_params,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            result = response.json()
            
            # 检查错误响应
            if "error_response" in result:
                error = result["error_response"]
                logger.error(f"API错误: {error}")
                raise Exception(f"拼多多API错误: {error.get('error_msg', '未知错误')}")
            
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP请求错误: {e}")
            raise
        except Exception as e:
            logger.error(f"请求异常: {e}")
            raise
    
    async def get_access_token(self, code: str) -> Dict[str, Any]:
        """获取access_token"""
        params = {
            "code": code,
            "grant_type": "authorization_code"
        }
        return await self._request("pdd.pop.auth.token.create", params)
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """刷新access_token"""
        params = {
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        return await self._request("pdd.pop.auth.token.refresh", params)
    
    async def get_conversation_list(self) -> Dict[str, Any]:
        """获取会话列表"""
        params = {}
        if self.access_token:
            params["access_token"] = self.access_token
        return await self._request("pdd.pop.chat.conversation.list", params)
    
    async def get_chat_messages(self, conversation_id: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取聊天消息"""
        params = {
            "conversation_id": conversation_id,
            "page": page,
            "page_size": page_size
        }
        if self.access_token:
            params["access_token"] = self.access_token
        return await self._request("pdd.pop.chat.message.list", params)
    
    async def send_message(self, conversation_id: str, content: str, msg_type: int = 1) -> Dict[str, Any]:
        """发送消息
        msg_type: 1-文本, 2-图片, 3-商品卡片
        """
        params = {
            "conversation_id": conversation_id,
            "content": content,
            "msg_type": msg_type
        }
        if self.access_token:
            params["access_token"] = self.access_token
        return await self._request("pdd.pop.chat.message.send", params)
    
    async def get_order_detail(self, order_sn: str) -> Dict[str, Any]:
        """获取订单详情"""
        params = {
            "order_sn": order_sn
        }
        if self.access_token:
            params["access_token"] = self.access_token
        return await self._request("pdd.order.detail.get", params)
    
    async def get_logistics_info(self, order_sn: str) -> Dict[str, Any]:
        """获取物流信息"""
        params = {
            "order_sn": order_sn
        }
        if self.access_token:
            params["access_token"] = self.access_token
        return await self._request("pdd.logistics.online.send", params)
    
    # ==================== 商品API ====================
    
    async def get_product_list(self, page: int = 1, page_size: int = 20, 
                               search_goods_name: Optional[str] = None,
                               goods_status: Optional[int] = None) -> Dict[str, Any]:
        """获取商品列表
        
        Args:
            page: 页码
            page_size: 每页数量
            search_goods_name: 商品名称搜索
            goods_status: 商品状态 (1-上架, 2-下架, 3-售罄, 4-已删除)
            
        Returns:
            商品列表响应
        """
        params = {
            "page": page,
            "page_size": page_size,
        }
        if search_goods_name:
            params["search_goods_name"] = search_goods_name
        if goods_status is not None:
            params["goods_status"] = goods_status
        if self.access_token:
            params["access_token"] = self.access_token
        return await self._request("pdd.goods.list.get", params)
    
    async def get_product_detail(self, goods_id: int) -> Dict[str, Any]:
        """获取商品详情
        
        Args:
            goods_id: 商品ID
            
        Returns:
            商品详情
        """
        params = {"goods_id": goods_id}
        if self.access_token:
            params["access_token"] = self.access_token
        return await self._request("pdd.goods.detail.get", params)
    
    async def update_product_price(self, goods_id: int, 
                                    sku_prices: list) -> Dict[str, Any]:
        """更新商品价格
        
        Args:
            goods_id: 商品ID
            sku_prices: SKU价格列表 [{"sku_id": xxx, "price": xxx}]
            
        Returns:
            更新结果
        """
        import json
        params = {
            "goods_id": goods_id,
            "sku_prices": json.dumps(sku_prices),
        }
        if self.access_token:
            params["access_token"] = self.access_token
        return await self._request("pdd.goods.price.update", params)
    
    async def update_product_stock(self, goods_id: int, 
                                    sku_stocks: list) -> Dict[str, Any]:
        """更新商品库存
        
        Args:
            goods_id: 商品ID
            sku_stocks: SKU库存列表 [{"sku_id": xxx, "stock": xxx}]
            
        Returns:
            更新结果
        """
        import json
        params = {
            "goods_id": goods_id,
            "sku_stocks": json.dumps(sku_stocks),
        }
        if self.access_token:
            params["access_token"] = self.access_token
        return await self._request("pdd.goods.stock.update", params)
    
    # ==================== 订单API ====================
    
    async def get_order_list(self, page: int = 1, page_size: int = 20,
                             start_time: Optional[int] = None,
                             end_time: Optional[int] = None,
                             order_status: Optional[int] = None) -> Dict[str, Any]:
        """获取订单列表
        
        Args:
            page: 页码
            page_size: 每页数量
            start_time: 下单开始时间(时间戳)
            end_time: 下单结束时间(时间戳)
            order_status: 订单状态 (1-待发货, 2-已发货, 3-已签收, 5-已取消)
            
        Returns:
            订单列表响应
        """
        params = {
            "page": page,
            "page_size": page_size,
        }
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        if order_status is not None:
            params["order_status"] = order_status
        if self.access_token:
            params["access_token"] = self.access_token
        return await self._request("pdd.order.list.get", params)
    
    async def ship_order(self, order_sn: str, logistics_id: int,
                         tracking_number: str) -> Dict[str, Any]:
        """发货
        
        Args:
            order_sn: 订单编号
            logistics_id: 物流公司ID
            tracking_number: 物流单号
            
        Returns:
            发货结果
        """
        params = {
            "order_sn": order_sn,
            "logistics_id": logistics_id,
            "tracking_number": tracking_number,
        }
        if self.access_token:
            params["access_token"] = self.access_token
        return await self._request("pdd.order.shipping.send", params)
    
    async def get_refund_list(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取退款列表
        
        Returns:
            退款列表响应
        """
        params = {
            "page": page,
            "page_size": page_size,
        }
        if self.access_token:
            params["access_token"] = self.access_token
        return await self._request("pdd.refund.list.increment.get", params)
    
    async def agree_refund(self, refund_id: int) -> Dict[str, Any]:
        """同意退款
        
        Args:
            refund_id: 退款ID
            
        Returns:
            操作结果
        """
        params = {"refund_id": refund_id}
        if self.access_token:
            params["access_token"] = self.access_token
        return await self._request("pdd.refund.agree", params)
    
    async def get_shop_info(self) -> Dict[str, Any]:
        """获取店铺信息
        
        Returns:
            店铺信息
        """
        params = {}
        if self.access_token:
            params["access_token"] = self.access_token
        return await self._request("pdd.mall.info.get", params)

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


# 创建全局客户端实例（可选）
pdd_client = PDDClient()
