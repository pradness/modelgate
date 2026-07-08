from redis.asyncio import Redis
redis: Redis | None = None

async def connect_redis():
    global redis
    redis = Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
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
