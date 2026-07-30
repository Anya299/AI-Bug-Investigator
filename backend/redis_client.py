import os
import redis

REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"

# Render's managed Redis/Key Value add-on gives you a single connection
# string (redis:// or rediss:// with the password baked in), not separate
# host/port/password variables. Prefer that when present; fall back to
# host/port for local dev against a plain `redis-server` with no auth.
REDIS_URL = os.getenv("REDIS_URL")

redis_client = None

if REDIS_ENABLED:
    if REDIS_URL:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    else:
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            password=os.getenv("REDIS_PASSWORD") or None,
            decode_responses=True
        )


def check_redis():
    if not REDIS_ENABLED or redis_client is None:
        return False

    try:
        return bool(redis_client.ping())
    except Exception as e:
        print("Redis Error:", e)  # <-- temporarily add this
        return False


def get_redis_status():
    if not REDIS_ENABLED or redis_client is None:
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