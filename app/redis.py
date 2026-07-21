from redis.asyncio import Redis
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
redis: Redis | None = None

async def connect_redis():
    global redis
    redis = Redis(
        host=os.getenv("REDIS_HOST") or "localhost",
        port=int(os.getenv("REDIS_PORT") or 6379),
        decode_responses=True,
        password=os.getenv("REDIS_PASSWORD")
    )
    await redis.ping()
    print("Redis connected")

def get_redis() -> Redis:
    if redis is None:
        raise RuntimeError("Redis not initialized")

    return redis

async def disconnect_redis():
    global redis
    if redis:
        await redis.aclose()
        print("Redis disconnected")
