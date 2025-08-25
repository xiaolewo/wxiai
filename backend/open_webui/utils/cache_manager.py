"""
高性能缓存管理器
提供多层缓存策略和性能优化功能
"""

import json
import hashlib
import time
import asyncio
from functools import wraps
from typing import Optional, Any, Dict, List, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """缓存配置"""

    default_ttl: int = 300  # 默认5分钟
    max_memory_items: int = 1000  # 内存缓存最大条目
    enable_compression: bool = False  # 启用数据压缩
    key_prefix: str = "wxiai"  # 缓存键前缀


class MemoryCache:
    """内存缓存实现"""

    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.access_times: Dict[str, float] = {}

    def get(self, key: str) -> Optional[Any]:
        """获取缓存项"""
        if key not in self.cache:
            return None

        item = self.cache[key]

        # 检查过期
        if time.time() > item["expires"]:
            self._remove(key)
            return None

        # 更新访问时间
        self.access_times[key] = time.time()
        return item["data"]

    def set(self, key: str, value: Any, ttl: int):
        """设置缓存项"""
        # 如果缓存已满，移除最久未访问的项
        if len(self.cache) >= self.max_size and key not in self.cache:
            self._evict_lru()

        self.cache[key] = {
            "data": value,
            "expires": time.time() + ttl,
            "created_at": time.time(),
        }
        self.access_times[key] = time.time()

    def delete(self, key: str):
        """删除缓存项"""
        self._remove(key)

    def _remove(self, key: str):
        """内部删除方法"""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)

    def _evict_lru(self):
        """移除最久未访问的项"""
        if not self.access_times:
            return

        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        self._remove(lru_key)

    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_times.clear()

    def stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": getattr(self, "_hit_rate", 0.0),
        }


class CacheManager:
    """统一缓存管理器"""

    def __init__(self, redis_client=None, config: CacheConfig = None):
        self.redis = redis_client
        self.config = config or CacheConfig()
        self.memory_cache = MemoryCache(self.config.max_memory_items)

        # 统计信息
        self.stats = {
            "redis_hits": 0,
            "redis_misses": 0,
            "memory_hits": 0,
            "memory_misses": 0,
            "sets": 0,
            "deletes": 0,
        }

    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [self.config.key_prefix, prefix]
        key_parts.extend(str(arg) for arg in args)

        if kwargs:
            # 对kwargs进行排序以确保一致性
            kwargs_str = json.dumps(kwargs, sort_keys=True, separators=(",", ":"))
            key_parts.append(hashlib.md5(kwargs_str.encode()).hexdigest()[:8])

        return ":".join(key_parts)

    async def get(self, key: str, use_memory: bool = True) -> Optional[Any]:
        """获取缓存值"""

        # 1. 先尝试从内存缓存获取
        if use_memory:
            memory_result = self.memory_cache.get(key)
            if memory_result is not None:
                self.stats["memory_hits"] += 1
                return memory_result
            self.stats["memory_misses"] += 1

        # 2. 从Redis获取
        if self.redis:
            try:
                redis_result = await self.redis.get(key)
                if redis_result:
                    self.stats["redis_hits"] += 1
                    data = json.loads(redis_result)

                    # 回填到内存缓存
                    if use_memory:
                        self.memory_cache.set(key, data, self.config.default_ttl)

                    return data
                else:
                    self.stats["redis_misses"] += 1
            except Exception as e:
                logger.error(f"Redis get error for key {key}: {e}")

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = None,
        use_memory: bool = True,
        use_redis: bool = True,
    ) -> bool:
        """设置缓存值"""
        ttl = ttl or self.config.default_ttl
        serialized_value = json.dumps(value, default=str, separators=(",", ":"))

        success = True

        # 设置到内存缓存
        if use_memory:
            self.memory_cache.set(key, value, ttl)

        # 设置到Redis
        if use_redis and self.redis:
            try:
                await self.redis.setex(key, ttl, serialized_value)
                self.stats["sets"] += 1
            except Exception as e:
                logger.error(f"Redis set error for key {key}: {e}")
                success = False

        return success

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        # 从内存缓存删除
        self.memory_cache.delete(key)

        # 从Redis删除
        if self.redis:
            try:
                await self.redis.delete(key)
                self.stats["deletes"] += 1
                return True
            except Exception as e:
                logger.error(f"Redis delete error for key {key}: {e}")
                return False

        return True

    async def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的缓存"""
        deleted_count = 0

        if self.redis:
            try:
                # 获取匹配的键
                keys = await self.redis.keys(pattern)
                if keys:
                    deleted_count = await self.redis.delete(*keys)
                    logger.info(
                        f"Deleted {deleted_count} keys matching pattern: {pattern}"
                    )
            except Exception as e:
                logger.error(f"Redis delete pattern error: {e}")

        return deleted_count

    async def clear_user_cache(self, user_id: str):
        """清理用户相关缓存"""
        patterns = [
            f"{self.config.key_prefix}:user_info:{user_id}:*",
            f"{self.config.key_prefix}:user_tasks:{user_id}:*",
            f"{self.config.key_prefix}:user_stats:{user_id}:*",
            f"{self.config.key_prefix}:user_credits:{user_id}:*",
        ]

        for pattern in patterns:
            await self.delete_pattern(pattern)

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_requests = (
            self.stats["redis_hits"]
            + self.stats["redis_misses"]
            + self.stats["memory_hits"]
            + self.stats["memory_misses"]
        )

        redis_hit_rate = self.stats["redis_hits"] / max(
            1, self.stats["redis_hits"] + self.stats["redis_misses"]
        )
        memory_hit_rate = self.stats["memory_hits"] / max(
            1, self.stats["memory_hits"] + self.stats["memory_misses"]
        )

        return {
            "total_requests": total_requests,
            "redis_hit_rate": redis_hit_rate,
            "memory_hit_rate": memory_hit_rate,
            "memory_cache": self.memory_cache.stats(),
            "counters": self.stats.copy(),
        }

    async def health_check(self) -> Dict[str, bool]:
        """健康检查"""
        status = {"memory_cache": True, "redis_cache": False}

        if self.redis:
            try:
                await self.redis.ping()
                status["redis_cache"] = True
            except Exception as e:
                logger.error(f"Redis health check failed: {e}")

        return status


# 缓存装饰器
def cache_result(
    prefix: str, ttl: int = None, use_memory: bool = True, key_func: Callable = None
):
    """缓存结果装饰器"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            from open_webui.main import app

            if not hasattr(app.state, "cache_manager"):
                # 如果没有缓存管理器，直接执行函数
                return await func(*args, **kwargs)

            cache_manager = app.state.cache_manager

            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_manager._make_key(prefix, *args, **kwargs)

            # 尝试从缓存获取
            cached_result = await cache_manager.get(cache_key, use_memory)
            if cached_result is not None:
                return cached_result

            # 执行函数
            result = await func(*args, **kwargs)

            # 存入缓存
            actual_ttl = ttl or cache_manager.config.default_ttl
            await cache_manager.set(cache_key, result, actual_ttl, use_memory)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 对于同步函数的处理
            return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def cache_invalidate(patterns: List[str]):
    """缓存失效装饰器"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from open_webui.main import app

            # 执行函数
            result = await func(*args, **kwargs)

            # 清理相关缓存
            if hasattr(app.state, "cache_manager"):
                cache_manager = app.state.cache_manager
                for pattern in patterns:
                    # 支持动态模式替换
                    if callable(pattern):
                        actual_pattern = pattern(*args, **kwargs)
                    else:
                        actual_pattern = pattern.format(*args, **kwargs)

                    await cache_manager.delete_pattern(actual_pattern)

            return result

        return wrapper

    return decorator


# 应用级缓存实例
cache_manager: Optional[CacheManager] = None


def init_cache_manager(redis_client=None, config: CacheConfig = None):
    """初始化缓存管理器"""
    global cache_manager
    cache_manager = CacheManager(redis_client, config)
    return cache_manager


def get_cache_manager() -> Optional[CacheManager]:
    """获取缓存管理器实例"""
    return cache_manager


# 常用缓存函数
@cache_result("user_info", ttl=600)  # 10分钟
async def get_cached_user_info(user_id: str):
    """缓存用户信息"""
    from open_webui.models.users import Users
    from open_webui.models.credits import Credits

    user = Users.get_user_by_id(user_id)
    if not user:
        return None

    credit = Credits.get_credit_by_user_id(user_id)

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "profile_image_url": user.profile_image_url,
        "credit": str(credit.credit if credit else "0.0000"),
        "last_active_at": user.last_active_at,
        "cached_at": time.time(),
    }


@cache_result("ai_config", ttl=1800)  # 30分钟
async def get_cached_ai_config(service_name: str):
    """缓存AI服务配置"""
    if service_name == "midjourney":
        from open_webui.models.midjourney import MJConfig

        config = MJConfig.get_config()
        return config.dict() if config else None
    elif service_name == "flux":
        from open_webui.models.flux import FluxConfig

        config = FluxConfig.get_config()
        return config.dict() if config else None
    # 添加其他服务...

    return None


@cache_result("model_list", ttl=3600)  # 1小时
async def get_cached_model_list():
    """缓存模型列表"""
    from open_webui.models.models import Models

    models = Models.get_all_models()
    return [model.dict() for model in models]


# 缓存预热函数
async def warm_up_cache():
    """缓存预热 - 在应用启动时调用"""
    try:
        # 预加载常用数据
        await get_cached_model_list()

        # 预加载AI服务配置
        services = ["midjourney", "flux", "dreamwork", "jimeng", "kling"]
        for service in services:
            await get_cached_ai_config(service)

        logger.info("Cache warm-up completed")
    except Exception as e:
        logger.error(f"Cache warm-up failed: {e}")
