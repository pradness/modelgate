from fastapi import HTTPException, status

from app.redis import get_redis

RATE_LIMIT = 100
WINDOW = 3600

async def check_rate_limit(api_key_id: int):
    key = f"rate_limit:{api_key_id}"
    redis = get_redis()
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, WINDOW)
    if count > RATE_LIMIT:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")