from pattern_matcher import find_matching_pattern
import json
import re
from enum import Enum

from fastapi import FastAPI, Request, status, Depends, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, field_validator

from config import get_settings
from logger import get_logger
from prompt import PROMPT_VERSION, SYSTEM_PROMPT, build_user_message

from database import SessionLocal
from models import BugReport, Analysis, User

from schemas import UserCreate, UserResponse

from routes.auth import verify_token, hash_password

from routes.auth import router as auth_router

from redis_client import check_redis, get_redis_status
from cache import (get_cached_analysis,set_cached_analysis,check_rate_limit
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


app.include_router(auth_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Schemas =====

class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class BugReportRequest(BaseModel):
    description: str = Field(..., description="What happened, expected vs actual.")
    stack_trace: str | None = Field(default=None, description="Optional error log.")
    language: str | None = Field(default=None, description="e.g. 'Python/FastAPI'.")
    severity: Severity | None = Field(default=None)

    @field_validator("description")
    @classmethod
    def description_not_blank(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("description must not be empty or whitespace-only")
        return cleaned

    @field_validator("stack_trace")
    @classmethod
    def strip_stack_trace(cls, v: str | None) -> str | None:
        return v.strip() or None if v else v


class BugAnalysisResponse(BaseModel):
    bug_summary: str
    root_cause: str
    investigation_steps: list[str]
    fix_recommendation: str
    prevention: str
    confidence_score: int = Field(default=0, ge=0, le=100)
    evidence: list[str] = Field(default_factory=list)
    prompt_version: str = PROMPT_VERSION


class ErrorResponse(BaseModel):
    error: str
    detail: str


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


# ===== Quality guard =====
#
# Bug-9-style failures aren't JSON parsing errors -- the JSON is valid,
# the schema matches, but the text inside the fields is incoherent
# (long runs of unrelated words with no real grammar). This heuristic
# catches that class of failure so we can retry instead of shipping
# garbage to a user or to the eval script.

# Common English function words. A coherent sentence has these
# sprinkled throughout; a degenerate word-salad output largely lacks them.
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
        return False  # too short to judge, don't false-positive

    lower_words = [w.lower() for w in words]

    # 1. Coherent English text has a healthy share of short function words.
    #    Word-salad output tends to be almost all "content" words strung together.
    common_ratio = sum(1 for w in lower_words if w in _COMMON_WORDS) / len(lower_words)

    # 2. Degenerate output tends to have unusually long average word length
    #    (rare/invented-sounding words) with few short connector words.
    avg_word_len = sum(len(w) for w in lower_words) / len(lower_words)

    # 3. Degenerate output is often a huge run-on: very few sentence breaks
    #    relative to length.
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
    """
    Small models sometimes produce JSON that's syntactically valid but
    slightly off-schema in predictable ways -- e.g. confidence_score as a
    range string like "40-69" instead of an int, or as a float. Rather than
    hard-failing on these known quirks, normalize them here. Anything not
    covered by these rules still fails validation as before.
    """
    if "confidence_score" in data:
        score = data["confidence_score"]
        if isinstance(score, str):
            # Handle "40-69" style ranges by taking the midpoint; handle
            # plain numeric strings like "75" directly.
            numbers = re.findall(r"\d+", score)
            if numbers:
                nums = [int(n) for n in numbers]
                data["confidence_score"] = sum(nums) // len(nums)
            else:
                data["confidence_score"] = 0
        elif isinstance(score, float):
            data["confidence_score"] = int(round(score))

    # Clamp into valid range rather than fail validation on an out-of-range int.
    if isinstance(data.get("confidence_score"), int):
        data["confidence_score"] = max(0, min(100, data["confidence_score"]))

    if "evidence" in data and isinstance(data["evidence"], str):
        # Model occasionally returns a single string instead of a list.
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


async def _call_model(bug: BugReportRequest, *, temperature: float) -> BugAnalysisResponse:
    client = AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        timeout=settings.request_timeout_seconds,
        max_retries=settings.max_retries,
    )

    user_message = build_user_message(
        description=bug.description,
        language=bug.language,
        severity=bug.severity.value if bug.severity else None,
        stack_trace=bug.stack_trace,
    )

    try:
        response = await client.chat.completions.create(
            model=settings.openrouter_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            # Lower max_tokens: the JSON schema here needs a few hundred
            # tokens at most. Giving the model room for 2000 tokens is what
            # let low-signal inputs (e.g. vague/legacy-code descriptions)
            # wander into degenerate, ungrounded text once it ran out of
            # anything real to say.
            max_tokens=settings.model_max_tokens,
            temperature=temperature,
            # Discourage repeating/rare-token runs, a common precursor to
            # word-salad degeneration.
            frequency_penalty=settings.model_frequency_penalty,
            presence_penalty=settings.model_presence_penalty,
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        logger.exception("Analyzer call failed")
        raise AnalyzerUpstreamError(str(exc))

    raw_text = response.choices[0].message.content

    if not raw_text:
        raise AnalyzerParsingError("Model returned an empty response.")

    result = parse_model_output(raw_text)
    result.prompt_version = PROMPT_VERSION

    if not result.investigation_steps:
        result.investigation_steps = [
            "Review logs",
            "Reproduce issue",
            "Inspect related code",
        ]

    return result


async def analyze_bug(bug: BugReportRequest) -> BugAnalysisResponse:
    """
    Calls the model, with a quality guard: if the response passes JSON/schema
    validation but reads as incoherent word-salad, retry once at a lower
    temperature before giving up. This is what prevents Bug-9-style output
    from ever reaching a user or the eval script.
    """
    last_error: Exception | None = None

    # First attempt at normal temperature, one retry at a much lower
    # (more conservative/deterministic) temperature if quality check fails.
    for attempt, temperature in enumerate(
        [settings.model_temperature, settings.model_temperature_retry]
    ):
        try:
            result = await _call_model(bug, temperature=temperature)
            _validate_response_quality(result)
            return result
        except AnalyzerQualityError as exc:
            logger.warning(
                "Attempt %d produced low-quality output, retrying: %s",
                attempt + 1, exc
            )
            last_error = exc
            continue
        except AnalyzerParsingError as exc:
            logger.warning(
                "Attempt %d produced malformed/off-schema output, retrying: %s",
                attempt + 1, exc
            )
            last_error = exc
            continue
        except AnalyzerUpstreamError:
            # Don't retry on upstream/network errors here; let the route
            # handler's existing error handling deal with those as before.
            raise

    # Both attempts failed (either quality check or schema validation).
    # Fail loudly rather than silently shipping garbage or a malformed
    # response -- this surfaces as a 502 the same way it did before.
    logger.error("Both generation attempts failed.")
    raise AnalyzerParsingError(
        "Model output failed validation after retry."
    ) from last_error


# ===== Error handlers =====

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error on %s: %s", request.url.path, exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="validation_error",
            detail="Your request did not pass validation. Check 'description' length and types.",
        ).model_dump(),
    )


@app.exception_handler(AnalyzerTimeoutError)
async def analyzer_timeout_handler(request: Request, exc: AnalyzerTimeoutError):
    logger.error("Analyzer timeout: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content=ErrorResponse(
            error="analysis_timeout",
            detail="The bug analysis took too long and timed out. Please try again.",
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
        ).model_dump(),
    )


@app.exception_handler(AnalyzerParsingError)
async def analyzer_parsing_handler(request: Request, exc: AnalyzerParsingError):
    logger.error("Analyzer parsing error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content=ErrorResponse(
            error="malformed_analysis",
            detail="The analysis result could not be parsed. Please try again.",
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
        ).model_dump(),
    )

def save_bug_analysis(bug: BugReportRequest, result: BugAnalysisResponse):
    db = SessionLocal()

    try:
        bug_report = BugReport(
            description=bug.description,
            stack_trace=bug.stack_trace,
            language=bug.language,
            severity=bug.severity.value if bug.severity else None,
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
            prompt_version=result.prompt_version,
            model_used=settings.openrouter_model
        )

        db.add(analysis)
        db.commit()

    except Exception as e:
        db.rollback()
        logger.error("Database save failed: %s", e)

    finally:
        db.close()

# ===== Routes =====

@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {
        "status": "ok",
        "service": settings.app_name,
        "prompt_version": PROMPT_VERSION,
        "redis": check_redis()
    }

@app.get("/cache/stats", tags=["meta"])
async def cache_stats():
    return get_redis_status()

@app.post(
    "/analyze-bug",
    response_model=BugAnalysisResponse,
    responses={
        422: {"model": ErrorResponse, "description": "Invalid input"},
        502: {"model": ErrorResponse, "description": "Upstream/parsing failure"},
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
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Try again later."
            )

        # ---- Cache check ----
        cached_result = get_cached_analysis(
            payload.description,
            payload.stack_trace,
            payload.language,
            payload.severity.value if payload.severity else None,
        )

        if cached_result:
            logger.info("Returning cached analysis")
            return BugAnalysisResponse(**cached_result)

        # ---- Cache MISS: Call AI ----
        result = await analyze_bug(payload)

        # ---- Save result into database ----
        save_bug_analysis(payload, result)

        # ---- Cache write ----
        set_cached_analysis(
            payload.description,
            result.model_dump(),
            payload.stack_trace,
            payload.language,
            payload.severity.value if payload.severity else None,
        )

        return result

    except AnalyzerParsingError as e:
        logger.error("Parsing error: %s", e)

        raise HTTPException(
            status_code=502,
            detail=str(e)
        )

    except AnalyzerUpstreamError as e:
        logger.error("Upstream error: %s", e)

        raise HTTPException(
            status_code=502,
            detail=str(e)
        )

    except AnalyzerTimeoutError as e:
        logger.error("Timeout error: %s", e)

        raise HTTPException(
            status_code=504,
            detail=str(e)
        )

    # Keep FastAPI HTTP errors (like rate limit 429) unchanged
    except HTTPException:
        raise

    except Exception as e:
        logger.exception("Unexpected error: %s", e)

        raise HTTPException(
            status_code=500,
            detail="Something went wrong during analysis"
        )