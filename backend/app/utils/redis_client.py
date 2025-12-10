import redis.asyncio as redis
import json
from typing import Optional, Any
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# 创建Redis连接池
redis_pool = redis.ConnectionPool.from_url(
    settings.redis_url,
    max_connections=50,
    decode_responses=True
)

# 创建Redis客户端
redis_client = redis.Redis(connection_pool=redis_pool)

async def get_redis() -> redis.Redis:
    """获取Redis客户端"""
    return redis_client

async def check_redis_connection() -> bool:
    """检查Redis连接"""
    try:
        await redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return False

async def get_cache(key: str) -> Optional[Any]:
    """获取缓存数据"""
    try:
        value = await redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.error(f"Error getting cache for key {key}: {e}")
        return None

async def set_cache(key: str, value: Any, ttl: int = 3600) -> bool:
    """设置缓存数据"""
    try:
        await redis_client.setex(key, ttl, json.dumps(value))
        return True
    except Exception as e:
        logger.error(f"Error setting cache for key {key}: {e}")
        return False

async def delete_cache(key: str) -> bool:
    """删除缓存数据"""
    try:
        await redis_client.delete(key)
        return True
    except Exception as e:
        logger.error(f"Error deleting cache for key {key}: {e}")
        return False

async def cache_exists(key: str) -> bool:
    """检查缓存是否存在"""
    try:
        return await redis_client.exists(key) > 0
    except Exception as e:
        logger.error(f"Error checking cache existence for key {key}: {e}")
        return False