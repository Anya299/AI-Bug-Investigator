import json
import hashlib

from logger import get_logger
from redis_client import redis_client
from prompt import PROMPT_VERSION
from config import get_settings


logger = get_logger(__name__)
settings = get_settings()

CACHE_TTL = 3600  # 1 hour


def generate_cache_key(
    description: str,
    stack_trace: str | None = None,
    language: str | None = None,
    severity: str | None = None,
) -> str:
    """
    Creates a deterministic Redis key from the FULL bug request, not just
    the description. Two requests with the same description but different
    stack traces, languages, or severities are treated as different bugs
    and get different cache entries -- otherwise we'd return a cached
    analysis that doesn't match the actual context of the new request.
    """
    normalized_parts = [
        (description or "").strip().lower(),
        (stack_trace or "").strip().lower(),
        (language or "").strip().lower(),
        (severity or "").strip().lower(),
    ]

    # Delimiter between fields so "desc=ab" + "trace=c" can't collide with
    # "desc=a" + "trace=bc" (simple concatenation would be ambiguous).
    normalized = "|".join(normalized_parts)

    hash_value = hashlib.md5(
        normalized.encode()
    ).hexdigest()

    return f"bug_analysis:{PROMPT_VERSION}:{settings.openrouter_model}:{hash_value}"


def get_cached_analysis(
    description: str,
    stack_trace: str | None = None,
    language: str | None = None,
    severity: str | None = None,
) -> dict | None:
    if redis_client is None:
        return None  # Redis disabled/unavailable -- always a cache miss

    key = generate_cache_key(description, stack_trace, language, severity)

    try:
        cached = redis_client.get(key)
    except Exception as e:
        # Redis being unavailable should never break the analysis flow --
        # treat it as a cache miss and fall through to the LLM call.
        logger.error("Redis cache read error (key=%s): %s", key, e)
        return None

    if cached:
        try:
            logger.info("Redis cache HIT (key=%s)", key)
            return json.loads(cached)
        except json.JSONDecodeError as e:
            # Corrupted cache entry -- log it and treat as a miss rather
            # than crashing the request on bad cached data.
            logger.error("Redis cache HIT but JSON decode failed (key=%s): %s", key, e)
            return None

    logger.info("Redis cache MISS (key=%s)", key)
    return None


def set_cached_analysis(
    description: str,
    result: dict,
    stack_trace: str | None = None,
    language: str | None = None,
    severity: str | None = None,
) -> None:
    if redis_client is None:
        return  # Redis disabled/unavailable -- silently skip caching

    key = generate_cache_key(description, stack_trace, language, severity)

    try:
        redis_client.setex(
            key,
            CACHE_TTL,
            json.dumps(result)
        )
        logger.info("Redis cache SET (key=%s, ttl=%ss)", key, CACHE_TTL)
    except Exception as e:
        # A failed cache write should not fail the request -- the user
        # still gets their analysis, it just won't be cached this time.
        logger.error("Redis cache SET failed (key=%s): %s", key, e)


async def check_rate_limit(user_id: str, limit: int = 100) -> bool:
    """
    Fail-open by design: if Redis is disabled or unreachable, rate limiting
    is simply not enforced rather than blocking every request. Every other
    Redis-touching function in this file already treats a Redis outage as
    "skip the feature, don't break the request" -- this one previously
    didn't, which meant a disabled/down Redis took the entire API down via
    an unhandled AttributeError on the very first check of every request.
    """
    if redis_client is None:
        return True

    key = f"rate_limit:{user_id}"

    try:
        current = redis_client.get(key)

        if current and int(current) >= limit:
            return False

        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, 3600)
        pipe.execute()

        return True
    except Exception as e:
        logger.error("Redis rate-limit check failed for user=%s: %s", user_id, e)
        return True