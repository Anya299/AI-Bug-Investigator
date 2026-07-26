import os
import redis

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)


def check_redis():
    try:
        return redis_client.ping()
    except Exception as e:
        print("Redis Error:", e)   # <-- temporarily add this
        return False

def get_redis_status():
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