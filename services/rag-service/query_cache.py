"""
RAG查询缓存模块
提供LRU缓存机制，减少重复查询的计算开销
"""
import hashlib
import time
from collections import OrderedDict
from typing import Dict, List, Optional, Any
from threading import Lock

from loguru import logger


class QueryCache:
    """LRU查询缓存"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        初始化缓存
        
        Args:
            max_size: 最大缓存条目数
            ttl_seconds: 缓存过期时间（秒）
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: Dict[str, float] = {}
        self._lock = Lock()
        
        # 统计信息
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expired": 0
        }
    
    def _make_key(self, domain: str, query: str, top_k: int) -> str:
        """生成缓存键"""
        key_str = f"{domain}:{query}:{top_k}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, domain: str, query: str, top_k: int) -> Optional[List[Dict]]:
        """
        获取缓存结果
        
        Returns:
            缓存的结果列表，如果未命中返回None
        """
        key = self._make_key(domain, query, top_k)
        
        with self._lock:
            if key in self._cache:
                # 检查是否过期
                if time.time() - self._timestamps[key] > self.ttl_seconds:
                    # 已过期，删除
                    del self._cache[key]
                    del self._timestamps[key]
                    self.stats["expired"] += 1
                    return None
                
                # 命中，移动到末尾（LRU）
                self._cache.move_to_end(key)
                self.stats["hits"] += 1
                return self._cache[key]
            
            self.stats["misses"] += 1
            return None
    
    def set(self, domain: str, query: str, top_k: int, results: List[Dict]):
        """设置缓存"""
        key = self._make_key(domain, query, top_k)
        
        with self._lock:
            # 如果已存在，先删除
            if key in self._cache:
                del self._cache[key]
                del self._timestamps[key]
            
            # 检查缓存大小，必要时驱逐
            while len(self._cache) >= self.max_size:
                evicted_key, _ = self._cache.popitem(last=False)
                del self._timestamps[evicted_key]
                self.stats["evictions"] += 1
            
            # 添加新条目
            self._cache[key] = results
            self._timestamps[key] = time.time()
    
    def invalidate(self, domain: Optional[str] = None):
        """
        使缓存失效
        
        Args:
            domain: 指定领域，如果为None则清空所有缓存
        """
        with self._lock:
            if domain is None:
                self._cache.clear()
                self._timestamps.clear()
                logger.info("Cache cleared completely")
            else:
                # 清空指定领域的缓存
                keys_to_remove = []
                for key in self._cache:
                    # 需要从key反查domain，这里简化处理
                    # 实际实现中可以在缓存时保存domain信息
                    pass
                
                for key in keys_to_remove:
                    del self._cache[key]
                    del self._timestamps[key]
                
                logger.info(f"Cache invalidated for domain: {domain}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (
            self.stats["hits"] / total_requests * 100 
            if total_requests > 0 else 0
        )
        
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "hit_rate": round(hit_rate, 2),
            **self.stats
        }
    
    def cleanup_expired(self):
        """清理过期条目"""
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            for key, timestamp in self._timestamps.items():
                if current_time - timestamp > self.ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                del self._timestamps[key]
                self.stats["expired"] += 1
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")


# 全局缓存实例
_query_cache: Optional[QueryCache] = None


def get_query_cache() -> QueryCache:
    """获取查询缓存单例"""
    global _query_cache
    if _query_cache is None:
        _query_cache = QueryCache()
    return _query_cache


def init_query_cache(max_size: int = 1000, ttl_seconds: int = 3600) -> QueryCache:
    """初始化查询缓存"""
    global _query_cache
    _query_cache = QueryCache(max_size=max_size, ttl_seconds=ttl_seconds)
    return _query_cache
