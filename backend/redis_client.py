import os
import redis

REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"

redis_client = None

if REDIS_ENABLED:
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=True
    )


def check_redis():
    if not REDIS_ENABLED:
        return False

    try:
        return redis_client.ping()
    except Exception as e:
        print("Redis Error:", e)
        return False


def get_redis_status():
    if not REDIS_ENABLED:
        return {
            "redis": False,
            "cache_status": "disabled"
        }

    try:
        redis_client.ping()

        return {
            "redis": True,
            "cache_status": "active"
        }

    except Exception:
        return {
            "redis": False,
            "cache_status": "inactive"
        }