from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    plan = Column(String(20), default="free")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    bug_reports = relationship(
        "BugReport",
        back_populates="user"
    )


class BugReport(Base):
    __tablename__ = "bug_reports"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )

    title = Column(String(255))
    language = Column(String(100))
    framework = Column(String(100))

    description = Column(Text)
    stack_trace = Column(Text)
    logs = Column(Text)

    severity = Column(String(50))
    status = Column(
        String(50),
        default="open"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    user = relationship(
        "User",
        back_populates="bug_reports"
    )

    analysis = relationship(
        "Analysis",
        back_populates="bug_report",
        uselist=False
    )


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)

    bug_report_id = Column(
        Integer,
        ForeignKey("bug_reports.id")
    )

    root_cause = Column(Text)
    explanation = Column(Text)

    reproduction_steps = Column(Text)
    suggested_fix = Column(Text)

    draft_test_case = Column(Text)

    confidence_score = Column(Float)

    prompt_version = Column(String(50))
    model_used = Column(String(100))

    response_time_ms = Column(Integer)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


    bug_report = relationship(
        "BugReport",
        back_populates="analysis"
    )
class BugKnowledgeBase(Base):
    __tablename__ = "bug_knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    language = Column(String, nullable=False)
    framework = Column(String, nullable=False)
    error_pattern = Column(String, nullable=False)
    root_cause = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
class BugPattern(Base):
    __tablename__ = "bug_patterns"

    id = Column(Integer, primary_key=True, index=True)

    error_type = Column(String(100), index=True)
    error_message = Column(Text)

    language = Column(String(100))
    framework = Column(String(100))

    root_cause = Column(Text)
    common_fix = Column(Text)

    tags = Column(String(255))

    success_rate = Column(Float, default=0.0)

    is_verified = Column(
        Boolean,
        default=False
    )

    usage_count = Column(
        Integer,
        default=0
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )    