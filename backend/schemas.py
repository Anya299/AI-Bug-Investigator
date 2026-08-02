import re
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

from datetime import datetime


class ProjectCreate(BaseModel):
    name: str

from pydantic import ConfigDict

class ProjectResponse(BaseModel):
    id: int
    name: str
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# =========================
# Bug Report Request Schema
# =========================

class BugReportRequest(BaseModel):
    project_id: int
    language: Optional[str] = Field(
        default=None,
        description="Programming language used in the project"
    )

    framework: Optional[str] = Field(
        default=None,
        description="Framework or library used"
    )

    environment: Optional[str] = Field(
        default=None,
        description="Operating system, runtime version, dependencies"
    )

    description: str = Field(
        ...,
        min_length=5,
        description="Short bug description"
    )

    stack_trace: Optional[str] = Field(
        default=None,
        description="Full stack trace or error logs, if available"
    )

    reproduction_steps: Optional[str] = Field(
        default=None,
        description="Steps to reproduce the issue"
    )

    expected_behavior: Optional[str] = Field(
        default=None,
        description="What the user expected to happen"
    )

    actual_behavior: Optional[str] = Field(
        default=None,
        description="What actually happened"
    )

    severity: Optional[str] = Field(
        default="medium",
        description="Bug severity level"
    )

    mode: Optional[str] = Field(
        default="quick",
        description="Analysis mode: quick or full"
    )

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value):
        if value not in ["quick", "full"]:
            raise ValueError("mode must be either 'quick' or 'full'")
        return value

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, value):
        allowed = ["low", "medium", "high", "critical"]
        if value not in allowed:
            raise ValueError(f"severity must be one of {allowed}")
        return value


# =========================
# Bug Analysis Response
# =========================

class BugAnalysisResponse(BaseModel):

    bug_summary: str
    root_cause: str
    investigation_steps: List[str]
    fix_recommendation: str
    prevention: str

    confidence_score: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Confidence based on available evidence"
    )

    evidence: List[str] = Field(
        default_factory=list,
        description="Stack trace lines or context supporting the analysis"
    )

    prompt_version: str
    source: str = "llm"


# =========================
# Auth Schemas
# =========================

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserCreate(BaseModel):

    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if not _EMAIL_RE.match(value):
            raise ValueError("must be a valid email address")
        return value.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("password must be at least 8 characters")
        return value


class UserResponse(BaseModel):

    id: int
    email: str

from pydantic import ConfigDict

class TokenResponse(BaseModel):

    access_token: str
    token_type: str = "bearer"


# =========================
# Error Response
# =========================

class ErrorResponse(BaseModel):

    error: str
    detail: str
    request_id: Optional[str] = None
    retryable: bool = False

class ProjectCreate(BaseModel):
    name: str


