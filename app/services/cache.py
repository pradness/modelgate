import hashlib
import json
from typing import Any

from app.redis import get_redis


def make_cache_key(
    model: str,
    version: str,
    payload: Any,
) -> str:
    payload_json = json.dumps(
        payload,
        sort_keys=True,
    )

    payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()

    return f"{model}:{version}:{payload_hash}"


async def get_prediction(cache_key: str) -> Any | None:
    redis = get_redis()
    cached = await redis.get(cache_key)
    if not cached:
        return None
    return json.loads(cached)


async def store_prediction(cache_key: str, prediction: Any, ttl: int = 3600) -> None:
    redis = get_redis()
    await redis.set(cache_key, json.dumps(prediction), ex=ttl)
