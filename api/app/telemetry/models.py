"""SQLAlchemy 2.0 models for telemetry storage."""

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TelemetryEvent(Base):
    """Individual telemetry event from a claude-kit session."""

    __tablename__ = "telemetry_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    session_id: Mapped[str] = mapped_column(String(36), index=True)
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_telemetry_events_user_timestamp", "user_id", "timestamp"),
        Index("ix_telemetry_events_user_session", "user_id", "session_id"),
    )


class SessionSummary(Base):
    """Aggregated summary for a completed claude-kit session."""

    __tablename__ = "session_summaries"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    session_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    plugins_loaded: Mapped[dict] = mapped_column(JSON, default=list)
    skills_invoked: Mapped[dict] = mapped_column(JSON, default=dict)
    hooks_fired: Mapped[dict] = mapped_column(JSON, default=dict)
    autorouter_matches: Mapped[int] = mapped_column(Integer, default=0)
    autorouter_misses: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    tool_uses: Mapped[dict] = mapped_column(JSON, default=dict)
    mcp_calls: Mapped[dict] = mapped_column(JSON, default=dict)
    compact_count: Mapped[int] = mapped_column(Integer, default=0)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_turns: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_session_summaries_user_start", "user_id", "start_time"),
    )
