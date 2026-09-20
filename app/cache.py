import os
import json
import redis.asyncio as redis

from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def cache_set(key, data, ttl: int = 30):
    await redis_client.setex(key, ttl, json.dumps(data))

async def cache_get(key):
    value = await redis_client.get(key)
    if value is None:
        return None
    return json.loads(value)

async def cache_delete(key):
    await redis_client.delete(key)