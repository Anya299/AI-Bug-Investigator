import json
from enum import Enum

from openai import AsyncOpenAI
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from config import get_settings
from logger import get_logger
from prompt import PROMPT_VERSION, SYSTEM_PROMPT, build_user_message
from database import SessionLocal
from models import BugReport, Analysis

logger = get_logger(__name__)
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Turns a raw bug description into a structured investigation report.",
    version="0.1.0",
)

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


# ===== Service layer =====

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

    try:
        return BugAnalysisResponse(**data)
    except Exception as exc:
        logger.error("Model JSON did not match expected schema: %s", exc)
        raise AnalyzerParsingError("Model output did not match the expected schema.") from exc


async def analyze_bug(bug: BugReportRequest) -> BugAnalysisResponse:
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
    max_tokens=1500,
    messages=[
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": user_message
        }
    ],
)
    except anthropic.APITimeoutError as exc:
        logger.error("Analyzer call timed out after %.1fs", settings.request_timeout_seconds)
        raise AnalyzerTimeoutError("The bug analysis request timed out.") from exc
    except (anthropic.RateLimitError, anthropic.APIStatusError, anthropic.APIConnectionError) as exc:
        logger.error("Analyzer upstream error: %s", exc)
        raise AnalyzerUpstreamError(f"Upstream analysis service error: {exc}") from exc

    raw_text = response.choices[0].message.content
    if not raw_text.strip():
        raise AnalyzerParsingError("Model returned an empty response.")

    logger.info(
        "Analysis complete | model=%s | prompt_v=%s | input_tokens=%s | output_tokens=%s",
        settings.openrouter_model,
        response.usage.prompt_tokens,
        response.usage.completion_tokens
    )
    return parse_model_output(raw_text)


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
    return {"status": "ok", "service": settings.app_name, "prompt_version": PROMPT_VERSION}


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
async def analyze_bug_endpoint(payload: BugReportRequest) -> BugAnalysisResponse:
    if len(payload.description) < settings.min_description_length:
        raise RequestValidationError([{
            "loc": ("body", "description"),
            "msg": f"description must be at least {settings.min_description_length} characters",
            "type": "value_error",
        }])
    if len(payload.description) > settings.max_description_length:
        raise RequestValidationError([{
            "loc": ("body", "description"),
            "msg": f"description must be under {settings.max_description_length} characters",
            "type": "value_error",
        }])

    logger.info(
    "Analyzing bug report (%d chars, language=%s)",
    len(payload.description),
    payload.language
    )

    result = await analyze_bug(payload)

    save_bug_analysis(payload, result)

    return result