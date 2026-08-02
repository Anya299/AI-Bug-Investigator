import time
import uuid

from routes import projects

from fastapi.encoders import jsonable_encoder

from metrics import get_metrics, record_request

from pattern_matcher import find_matching_pattern, record_pattern_usage
from confidence import calculate_confidence
import json
import re
from enum import Enum

from fastapi import FastAPI, Request, status, Depends, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from openai import AsyncOpenAI, APITimeoutError
from pydantic import BaseModel, Field

from schemas import BugReportRequest, BugAnalysisResponse

from config import get_settings
from logger import get_logger
from prompt import PROMPT_VERSION, SYSTEM_PROMPT, build_user_message

from database import SessionLocal, check_database
from models import BugReport, Analysis, User, KnowledgeEntry

from schemas import UserCreate, UserResponse

from routes.auth import verify_token, hash_password

from routes.auth import router as auth_router

from redis_client import get_redis_status
from cache import get_cached_analysis, set_cached_analysis


from circuit_breaker import (
    is_circuit_open,
    record_failure,
    record_success
)

logger = get_logger(__name__)
settings = get_settings()

if settings.is_free_tier_model:
    logger.warning(
        "Running on a free-tier OpenRouter model (%s). Free-tier models are "
        "more prone to incoherent/degenerate output on vague inputs. The "
        "quality guard will retry once, but consider a low-cost paid model "
        "(e.g. openai/gpt-4o-mini, anthropic/claude-3-5-haiku) before "
        "presenting this to users or in a demo.",
        settings.openrouter_model,
    )
elif settings.is_small_model:
    logger.info(
        "Running on a smaller model (%s). The quality guard may retry more "
        "often on vague/underspecified bug reports than it would on a "
        "larger model -- this is expected, not a bug.",
        settings.openrouter_model,
    )


app = FastAPI(
    title=settings.app_name,
    description="Turns a raw bug description into a structured investigation report.",
    version="0.1.0",
)

def get_real_client_ip(request: Request) -> str:
    """
    Render (and most PaaS platforms) terminate TLS at a reverse proxy, so
    request.client.host is the proxy's internal IP -- identical for every
    user. Read X-Forwarded-For instead, which the proxy sets to the real
    client IP. Used only as a fallback key for requests that never reach
    an authenticated identity (see get_user_identifier below).
    """
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return get_remote_address(request)


def get_user_identifier(request: Request) -> str:
    """
    SlowAPI's key_func only ever receives `request`, so it cannot call
    Depends(verify_token) itself. Instead, require_user_and_tag_request
    (used as the auth Depends on protected routes) runs first as part of
    FastAPI's normal dependency resolution and stashes the authenticated
    user id on request.state.user_id. By the time the limiter wrapper
    runs, that value is already present -- so authenticated calls are
    rate-limited per user, not per IP, and a shared office/NAT IP or a
    frontend dev testing repeatedly won't collide with other users.
    """
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    # No authenticated identity on the request (e.g. auth dependency
    # hasn't run yet for this route, or route is intentionally public).
    # Fall back to IP so the endpoint still has *some* protection.
    return f"ip:{get_real_client_ip(request)}"


limiter = Limiter(
    key_func=get_user_identifier,
    storage_uri=settings.redis_url
)
app.state.limiter = limiter


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Single source of truth for 429s (SlowAPI is now the only rate limiter --
    the old Redis check_rate_limit() has been removed to stop double
    rate-limiting the same request). Returns the app's standard ErrorResponse
    shape and injects Retry-After / X-RateLimit-* headers using SlowAPI's own
    header helper, so clients know exactly when they can retry.
    """
    response = JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=ErrorResponse(
            error="rate_limit_exceeded",
            detail="Too many requests. Please wait a moment and try again.",
            request_id=getattr(request.state, "request_id", None),
            retryable=True,
        ).model_dump(),
    )
    # Adds Retry-After, X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
    return request.app.state.limiter._inject_headers(response, request.state.view_rate_limit)


app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Required so SlowAPI's Limiter actually tracks/enforces request counts
# and attaches rate-limit headers. Without this, @limiter.limit(...)
# decorators are effectively inert.
app.add_middleware(SlowAPIMiddleware)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):

    start_time = time.time()
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)

    latency_ms = round((time.time() - start_time) * 1000, 2)

    logger.info(
        "request_completed | request_id=%s method=%s path=%s status_code=%s latency_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        latency_ms,
    )

    record_request(response.status_code, latency_ms)
    response.headers["X-Request-ID"] = request_id

    return response


app.include_router(auth_router)
app.include_router(projects.router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Schemas =====

class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ErrorResponse(BaseModel):
    error: str
    detail: str
    request_id: str | None = None
    retryable: bool = False


# ===== Service-layer exceptions =====

class AnalyzerError(Exception):
    pass


class AnalyzerTimeoutError(AnalyzerError):
    pass


class AnalyzerUpstreamError(AnalyzerError):
    pass


class AnalyzerParsingError(AnalyzerError):
    pass


class AnalyzerQualityError(AnalyzerError):
    """Raised when the model returns syntactically valid JSON that is
    semantically garbage (word-salad / degenerate generation)."""
    pass


class DatabaseUnavailableError(Exception):
    pass


class CircuitOpenError(Exception):
    pass


# ===== Quality guard =====

_COMMON_WORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "is", "are", "was",
    "for", "on", "with", "this", "that", "it", "be", "as", "by", "at",
    "from", "which", "will", "can", "should", "would", "has", "have",
    "not", "if", "then", "so", "may", "these", "their", "such",
}


def _looks_like_gibberish(text: str) -> bool:
    if not text:
        return False

    words = re.findall(r"[A-Za-z']+", text)
    if len(words) < 6:
        return False

    lower_words = [w.lower() for w in words]

    common_ratio = sum(1 for w in lower_words if w in _COMMON_WORDS) / len(lower_words)
    avg_word_len = sum(len(w) for w in lower_words) / len(lower_words)
    sentence_breaks = len(re.findall(r"[.!?]", text))
    words_per_break = len(words) / max(sentence_breaks, 1)

    is_suspicious = (
        common_ratio < 0.12
        and avg_word_len > 6.5
        and words_per_break > 40
    )
    return is_suspicious


def _validate_response_quality(result: "BugAnalysisResponse") -> None:
    combined_text = " ".join([
        result.bug_summary,
        result.root_cause,
        " ".join(result.investigation_steps),
        result.fix_recommendation,
        result.prevention,
    ])
    if _looks_like_gibberish(combined_text):
        raise AnalyzerQualityError(
            "Model output failed coherence check (likely degenerate generation)."
        )


# ===== Service layer =====

def _coerce_model_output(data: dict) -> dict:
    if "confidence_score" in data:
        score = data["confidence_score"]
        if isinstance(score, str):
            numbers = re.findall(r"\d+", score)
            if numbers:
                nums = [int(n) for n in numbers]
                data["confidence_score"] = sum(nums) // len(nums)
            else:
                data["confidence_score"] = 0
        elif isinstance(score, float):
            data["confidence_score"] = int(round(score))

    if isinstance(data.get("confidence_score"), int):
        data["confidence_score"] = max(0, min(100, data["confidence_score"]))

    if "evidence" in data and isinstance(data["evidence"], str):
        data["evidence"] = [data["evidence"]] if data["evidence"] else []

    if "investigation_steps" in data and isinstance(data["investigation_steps"], str):
        data["investigation_steps"] = [data["investigation_steps"]] if data["investigation_steps"] else []

    return data


def parse_model_output(raw_text: str) -> BugAnalysisResponse:
    text = raw_text.strip()

    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.error("Model output was not valid JSON: %s", exc)
        raise AnalyzerParsingError("Model did not return valid JSON.") from exc

    data = _coerce_model_output(data)

    try:
        return BugAnalysisResponse(**data)
    except Exception as exc:
        logger.error("Model JSON did not match expected schema: %s", exc)
        raise AnalyzerParsingError(
            "Model output did not match the expected schema."
        ) from exc


def _response_from_pattern(pattern: KnowledgeEntry, bug: BugReportRequest) -> BugAnalysisResponse:
    """
    Builds an instant response straight from a verified BugPattern, no LLM
    call involved. This is what makes "Quick fix" genuinely fast (and
    free) for bugs we've already solved before.
    """
    confidence = calculate_confidence(
        stack_trace=bug.stack_trace,
        description=bug.description,
        framework=bug.framework,
        environment=bug.environment,
        reproduction_steps=bug.reproduction_steps,
        expected_behavior=bug.expected_behavior,
        actual_behavior=bug.actual_behavior,
        pattern_match=True,
    )

    return BugAnalysisResponse(
        bug_summary=f"Matches known pattern: {pattern.error_type}",
        root_cause=pattern.root_cause or "See matched pattern for details.",
        investigation_steps=[
            f"Confirm the symptom matches: {pattern.error_type}",
            "Apply the fix below and check the reported behavior clears",
            "Add a regression test so this doesn't silently return",
        ],
        fix_recommendation=pattern.common_fix or "Apply the standard fix for this pattern.",
        prevention="Add a regression test covering this pattern; monitor for recurrence.",
        confidence_score=confidence,
        evidence=[f"Matched verified pattern: {pattern.error_type}"],
        prompt_version=f"pattern-match:{pattern.id}",
        source="pattern_match",
    )


async def _call_model(
    bug: BugReportRequest,
    *,
    temperature: float,
    pattern_hint: KnowledgeEntry | None = None,
) -> BugAnalysisResponse:

    if is_circuit_open():
        logger.warning("Circuit breaker open. Skipping AI request.")
        raise CircuitOpenError()

    client = AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        timeout=settings.request_timeout_seconds,
        max_retries=settings.max_retries,
    )

    user_message = build_user_message(
        description=bug.description,
        language=bug.language,
        severity=bug.severity if bug.severity else None,
        stack_trace=bug.stack_trace,
        framework=bug.framework,
        environment=bug.environment,
        reproduction_steps=bug.reproduction_steps,
        expected_behavior=bug.expected_behavior,
        actual_behavior=bug.actual_behavior,
        mode=bug.mode or "quick",
        pattern_hint=pattern_hint,
    )

    try:
        response = await client.chat.completions.create(
            model=settings.openrouter_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=settings.model_max_tokens,
            temperature=temperature,
            frequency_penalty=settings.model_frequency_penalty,
            presence_penalty=settings.model_presence_penalty,
            response_format={"type": "json_object"},
        )
    except APITimeoutError:
        logger.exception("Analyzer request timed out")
        raise AnalyzerTimeoutError()

    except Exception as exc:
        record_failure()
        logger.exception("Analyzer call failed")
        raise AnalyzerUpstreamError(str(exc))

    raw_text = response.choices[0].message.content

    if not raw_text:
        raise AnalyzerParsingError("Model returned an empty response.")

    result = parse_model_output(raw_text)

    record_success()

    result.prompt_version = PROMPT_VERSION
    result.source = "llm"

    # The model's own confidence_score is self-reported and inconsistent
    # across calls -- replace it with a score computed directly from what
    # evidence was actually supplied, so it means the same thing every time.
    result.confidence_score = calculate_confidence(
        stack_trace=bug.stack_trace,
        description=bug.description,
        framework=bug.framework,
        environment=bug.environment,
        reproduction_steps=bug.reproduction_steps,
        expected_behavior=bug.expected_behavior,
        actual_behavior=bug.actual_behavior,
        pattern_match=pattern_hint is not None,
    )

    if not result.investigation_steps:
        result.investigation_steps = [
            "Review logs",
            "Reproduce issue",
            "Inspect related code",
        ]

    return result


async def analyze_bug(
    bug: BugReportRequest,
    pattern_hint: KnowledgeEntry | None = None,
) -> BugAnalysisResponse:
    """
    Calls the model, with a quality guard: if the response passes JSON/schema
    validation but reads as incoherent word-salad, retry once at a lower
    temperature before giving up.
    """
    last_error: Exception | None = None

    for attempt, temperature in enumerate(
        [settings.model_temperature, settings.model_temperature_retry]
    ):
        try:
            result = await _call_model(bug, temperature=temperature, pattern_hint=pattern_hint)
            _validate_response_quality(result)
            return result
        except AnalyzerQualityError as exc:
            logger.warning("Attempt %d produced low-quality output, retrying: %s", attempt + 1, exc)
            last_error = exc
            continue
        except AnalyzerParsingError as exc:
            logger.warning("Attempt %d produced malformed/off-schema output, retrying: %s", attempt + 1, exc)
            last_error = exc
            continue
        except AnalyzerUpstreamError:
            raise
        except AnalyzerTimeoutError:
            raise
        except CircuitOpenError:
            raise

    logger.error("Both generation attempts failed.")
    raise AnalyzerParsingError(
        "Model output failed validation after retry."
    ) from last_error


# ===== Error handlers =====

@app.exception_handler(AnalyzerParsingError)
async def analyzer_parsing_handler(request: Request, exc: AnalyzerParsingError):
    # This fires whenever the model's JSON doesn't match BugAnalysisResponse
    # -- most commonly a prompt.py / main.py schema mismatch (SYSTEM_PROMPT
    # asking for different fields than BugAnalysisResponse requires) rather
    # than a transient model issue. Logged at error level since it usually
    # means something needs a code fix, not a retry.
    logger.error("Analyzer parsing/schema error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content=ErrorResponse(
            error="parsing_error",
            detail="The analysis response didn't match the expected format. Please try again.",
            request_id=request.state.request_id,
        ).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error on %s: %s", request.url.path, exc.errors())

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
           "error": "validation_error",
           "detail": jsonable_encoder(exc.errors())
        }
    )
    


@app.exception_handler(AnalyzerUpstreamError)
async def analyzer_upstream_handler(request: Request, exc: AnalyzerUpstreamError):
    logger.error("Analyzer upstream error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content=ErrorResponse(
            error="upstream_error",
            detail="The analysis provider returned an error. Please try again shortly.",
            request_id=request.state.request_id,
        ).model_dump(),
    )


@app.exception_handler(AnalyzerTimeoutError)
async def analyzer_timeout_handler(request: Request, exc: AnalyzerTimeoutError):
    logger.error("Analyzer timeout: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content=ErrorResponse(
            error="timeout",
            detail="The analysis request timed out. Please try again.",
            request_id=request.state.request_id,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="internal_error",
            detail="Something went wrong on our end. Please try again.",
            request_id=request.state.request_id,
        ).model_dump(),
    )


@app.exception_handler(DatabaseUnavailableError)
async def database_error_handler(request: Request, exc: DatabaseUnavailableError):
    logger.error("Database unavailable: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=ErrorResponse(
            error="database_unavailable",
            detail="Database service is temporarily unavailable.",
            request_id=request.state.request_id,
            retryable=True,
        ).model_dump(),
    )


@app.exception_handler(CircuitOpenError)
async def circuit_open_handler(request: Request, exc: CircuitOpenError):
    return JSONResponse(
        status_code=503,
        content=ErrorResponse(
            error="service_unavailable",
            detail="AI service temporarily unavailable. Please retry later.",
            request_id=request.state.request_id,
            retryable=True,
        ).model_dump(),
    )


def save_bug_analysis(bug: BugReportRequest, result: BugAnalysisResponse):
    try:
        db = SessionLocal()
    except Exception as e:
        logger.exception("Database connection failed")
        raise DatabaseUnavailableError(
            "Database is currently unavailable"
        ) from e

    try:
        bug_report = BugReport(
            project_id=bug.project_id,
            title="Bug Report",
            description=bug.description,
            stack_trace=bug.stack_trace,
            language=bug.language,
            framework=bug.framework,
            severity=bug.severity,
            status="open"
        )

        db.add(bug_report)
        db.commit()
        db.refresh(bug_report)


        analysis = Analysis(
            bug_report_id=bug_report.id,

            root_cause=result.root_cause,

            # map BugAnalysisResponse fields
            explanation=result.bug_summary,

            reproduction_steps="\n".join(
                result.investigation_steps
            ),

            suggested_fix=result.fix_recommendation,

            draft_test_case=None,

            confidence_score=result.confidence_score,

            prompt_version=result.prompt_version,

            model_used=settings.openrouter_model,

            response_time_ms=None
        )

        db.add(analysis)
        db.commit()
        db.refresh(analysis)

    except Exception:
        db.rollback()
        logger.exception("Failed to save bug analysis")
        raise

    finally:
        db.close()


# ===== Auth dependency wrapper (feeds the per-user rate limiter) =====

def extract_user_identifier(user_data) -> str | None:
    """
    Normalizes whatever an auth dependency returns into a single stable
    string identifier, without assuming a fixed shape. verify_token()
    implementations tend to drift over a project's life -- plain string,
    JWT payload dict, ORM User object -- and bracket-indexing a shape
    that doesn't match (e.g. dict['user_id'] when the dict only has
    'sub', or indexing a plain string) is exactly what produces crashes
    like "KeyError: user_id". Every branch below reads with .get()/
    getattr() so a missing key/attribute returns None instead of raising.
    Returns None if no usable identifier could be found.
    """
    if user_data is None:
        return None

    # Plain string identifier -- current verify_token() returns the
    # user's email extracted from the JWT "sub" claim.
    if isinstance(user_data, str):
        return user_data

    # SQLAlchemy ORM User instance.
    if isinstance(user_data, User):
        if getattr(user_data, "id", None) is not None:
            return str(user_data.id)
        return getattr(user_data, "email", None)

    # Dict-shaped payload (e.g. a raw decoded JWT, or {"user_id": ...},
    # or {"id": ...}). Check every key we might reasonably find an
    # identifier under, in priority order -- .get() never raises.
    if isinstance(user_data, dict):
        for key in ("user_id", "id", "sub", "email"):
            value = user_data.get(key)
            if value:
                return str(value)
        return None

    # Fallback for any other object shape (e.g. a Pydantic user model).
    user_id = getattr(user_data, "id", None)
    if user_id is not None:
        return str(user_id)

    email = getattr(user_data, "email", None)
    if email is not None:
        return str(email)

    return None


async def require_user_and_tag_request(
    request: Request,
    current_user = Depends(verify_token),
) -> str:
    """
    Thin wrapper around verify_token. FastAPI resolves this (and its
    nested verify_token dependency) before calling the route handler,
    so request.state.user_id is guaranteed to be set before SlowAPI's
    get_user_identifier key_func runs. Use this in place of
    Depends(verify_token) on any route that should be rate-limited
    per-user instead of per-IP.

    current_user is normalized through extract_user_identifier() before
    being stored, so this never crashes regardless of what verify_token()
    returns -- str, dict, or a User ORM object -- and stays safe even if
    verify_token()'s return shape changes later.
    """
    identifier = extract_user_identifier(current_user)

    if identifier is None:
        # Auth succeeded (verify_token didn't raise) but we couldn't pull
        # a usable identifier out of whatever it returned. Don't crash the
        # request over a rate-limiting concern -- just fall back to IP-based
        # limiting for this call and log it so the shape mismatch gets fixed.
        logger.warning(
            "require_user_and_tag_request: could not extract a user "
            "identifier from verify_token() output (type=%s); falling "
            "back to IP-based rate limiting for this request.",
            type(current_user).__name__,
        )
    else:
       request.state.user_id = identifier

    return current_user

# ===== Routes =====

@app.get("/health", tags=["meta"])
async def health() -> dict:
    redis_state = get_redis_status()
    database_status = check_database()

    redis_disabled = redis_state["cache_status"] == "disabled"
    redis_up = redis_state["redis"]

    if redis_disabled:
        redis_label = "disabled"
    elif redis_up:
        redis_label = "up"
    else:
        redis_label = "down"

    # A disabled Redis is an expected, working configuration -- it should
    # never make the service look "degraded". Only an unreachable Redis
    # that's supposed to be enabled counts as degraded.
    is_healthy = database_status and (redis_disabled or redis_up)

    return {
        "status": "healthy" if is_healthy else "degraded",
        "service": settings.app_name,
        "dependencies": {
            "redis": redis_label,
            "database": "up" if database_status else "down"
        },
        "prompt_version": PROMPT_VERSION
    }


@app.get("/cache/stats", tags=["meta"])
async def cache_stats():
    return get_redis_status()


@app.get("/stats", tags=["meta"])
async def stats():
    return get_metrics()


# NOTE: @app.post(...) MUST be the outer decorator and @limiter.limit(...)
# must be the inner one (closest to the function). SlowAPI wraps the
# function it decorates; if @limiter.limit sits above @app.post, FastAPI
# registers the raw unlimited function as the actual route handler and
# the limiter never runs, which is why requests were always returning 200.
@app.post(
    "/analyze-bug",
    response_model=BugAnalysisResponse,
    responses={
        422: {"model": ErrorResponse, "description": "Invalid input"},
        502: {"model": ErrorResponse, "description": "Upstream/parsing failure"},
        503: {"model": ErrorResponse, "description": "Database unavailable"},
        504: {"model": ErrorResponse, "description": "Analysis timed out"},
    },
    tags=["analysis"],
)
@limiter.limit("3/minute")
async def analyze_bug_endpoint(
    request: Request,
    payload: BugReportRequest,
    current_user: str = Depends(require_user_and_tag_request),
) -> BugAnalysisResponse:
    try:
        # ---- Cache check ----
        cached_result = get_cached_analysis(
            payload.description,
            payload.stack_trace,
            payload.language,
            payload.severity if payload.severity else None,
            payload.mode,
        )

        if cached_result:
            logger.info("Returning cached analysis")
            cached_result.setdefault("source", "cache")
            return BugAnalysisResponse(**cached_result)

        # ---- Pattern match check ----
        # Quick mode: a verified pattern match is used directly, skipping
        # the LLM call entirely -- this is the actual speed advantage of
        # "quick fix" over "full investigation".
        # Full mode: a match is still looked up, but only as grounding
        # context passed into the LLM prompt, not as a shortcut.
        matched_pattern = find_matching_pattern(
            payload.stack_trace or payload.description,
            language=payload.language,
            framework=payload.framework,
        )

        if matched_pattern and matched_pattern.is_verified and payload.mode == "quick":
            result = _response_from_pattern(matched_pattern, payload)
            record_pattern_usage(matched_pattern.id)
        else:
            if matched_pattern:
                record_pattern_usage(matched_pattern.id)
            result = await analyze_bug(payload, pattern_hint=matched_pattern)

        # ---- Save result into database ----
        save_bug_analysis(payload, result)

        # ---- Cache write ----
        set_cached_analysis(
            payload.description,
            result.model_dump(),
            payload.stack_trace,
            payload.language,
            payload.severity if payload.severity else None,
            payload.mode,
        )

        return result

    except AnalyzerParsingError:
        raise
    except AnalyzerUpstreamError:
        raise
    except AnalyzerTimeoutError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        raise HTTPException(status_code=500, detail="Something went wrong during analysis")