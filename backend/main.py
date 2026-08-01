import time
import uuid

from routes import projects

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
from cache import (get_cached_analysis, set_cached_analysis, check_rate_limit)


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
            explanation=result.bug_summary,
            reproduction_steps="\n".join(result.investigation_steps),
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

    except Exception as e:
        db.rollback()
        logger.exception("Failed to save bug analysis")
        raise

    finally:
        db.close()

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


def _response_from_pattern(pattern: KnowledgeEntry, bug: BugReportRequest)-> BugAnalysisResponse:
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
    pattern_hint: BugPattern | None = None,
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
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="validation_error",
            detail="Your request did not pass validation. Check 'description' length and types.",
            request_id=request.state.request_id,
        ).model_dump(),
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
async def analyze_bug_endpoint(
    payload: BugReportRequest,
    current_user: str = Depends(verify_token)
) -> BugAnalysisResponse:

    try:
        # ---- Rate limit check ----
        allowed = await check_rate_limit(current_user)
        if not allowed:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

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