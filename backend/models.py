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

    projects = relationship(
        "Project",
        back_populates="owner"
    )


class Project(Base):
    __tablename__ = "projects"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(255),
        nullable=False
    )

    owner_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    owner = relationship(
        "User",
        back_populates="projects"
    )

    bug_reports = relationship(
        "BugReport",
        back_populates="project"
    )


class KnowledgeEntry(Base):
    __tablename__ = "knowledge_entries"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    type = Column(
        String(50),
        default="bug_fix",
        nullable=False
    )

    error_type = Column(
        String(100),
        index=True
    )

    error_message = Column(Text)

    language = Column(String(100))

    framework = Column(String(100))

    root_cause = Column(Text)

    common_fix = Column(Text)

    tags = Column(String(255))

    success_rate = Column(
        Float,
        default=0.0
    )

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


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)

    bug_report_id = Column(
        Integer,
        ForeignKey("bug_reports.id")
    )

    knowledge_entry_id = Column(
        Integer,
        ForeignKey("knowledge_entries.id")
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

    bug_report = relationship("BugReport", back_populates="analyses")
    knowledge_entry = relationship("KnowledgeEntry")


class BugKnowledgeBase(Base):
    __tablename__ = "bug_knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    language = Column(String, nullable=False)
    framework = Column(String, nullable=False)
    error_pattern = Column(String, nullable=False)
    root_cause = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)


    user = relationship("User")


class BugReport(Base):
    __tablename__ = "bug_reports"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False
    )

    title = Column(String(255))
    description = Column(Text)
    stack_trace = Column(Text)
    logs = Column(Text)
    language = Column(String(100))
    framework = Column(String(100))
    severity = Column(String(50))
    status = Column(String(50))

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    project = relationship("Project", back_populates="bug_reports")
    analyses = relationship("Analysis", back_populates="bug_report")