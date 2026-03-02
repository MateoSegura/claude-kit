"""Pydantic request/response schemas for telemetry."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

# --- Enums ---


class EventType(StrEnum):
    """Valid telemetry event types."""

    SESSION_START = "session.start"
    SESSION_END = "session.end"
    SESSION_ERROR = "session.error"
    SESSION_RESULT = "session.result"
    SESSION_COMPACT = "session.compact"
    PLUGIN_LOADED = "plugin.loaded"
    SKILL_INVOKED = "skill.invoked"
    HOOK_FIRED = "hook.fired"
    AUTOROUTER_MATCH = "autorouter.match"
    AUTOROUTER_MISS = "autorouter.miss"
    VALIDATION_RESULT = "validation.result"
    TURN_COMPLETED = "turn.completed"
    TOOL_USED = "tool.used"
    TOOL_RESULT = "tool.result"
    MESSAGE_ASSISTANT = "message.assistant"
    MESSAGE_SYSTEM = "message.system"


class MetricsPeriod(StrEnum):
    """Aggregation period for metrics."""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"


# --- Request schemas ---


class TelemetryEventInput(BaseModel):
    """A single event in an ingest batch."""

    event_type: EventType
    timestamp: datetime
    payload: dict = Field(default_factory=dict)


class IngestRequest(BaseModel):
    """Batched telemetry event ingest request."""

    session_id: str = Field(min_length=1, max_length=36)
    events: list[TelemetryEventInput] = Field(min_length=1, max_length=1000)


# --- Response schemas ---


class IngestResponse(BaseModel):
    """Response after successful telemetry ingestion."""

    accepted: int
    session_id: str


class SessionSummaryResponse(BaseModel):
    """Summary of a single session."""

    session_id: str
    start_time: datetime
    end_time: datetime | None
    duration_s: float | None
    plugins_loaded: list[str]
    skills_invoked: dict[str, int]
    hooks_fired: dict[str, int]
    autorouter_matches: int
    autorouter_misses: int
    total_tokens_in: int
    total_tokens_out: int
    estimated_cost_usd: float
    tool_uses: dict[str, int] = Field(default_factory=dict)
    mcp_calls: dict[str, int] = Field(default_factory=dict)
    compact_count: int = 0
    model: str | None = None
    cost_usd: float | None = None
    total_turns: int = 0

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    """Paginated list of session summaries."""

    sessions: list[SessionSummaryResponse]
    total: int
    page: int
    per_page: int


class SessionDetailResponse(SessionSummaryResponse):
    """Session detail with event count."""

    event_count: int


class EventResponse(BaseModel):
    """A single telemetry event in query results."""

    id: str
    event_type: str
    timestamp: datetime
    payload: dict

    model_config = {"from_attributes": True}


class SessionEventsResponse(BaseModel):
    """Paginated list of events for a session."""

    events: list[EventResponse]
    total: int
    page: int
    per_page: int


class SkillUsageItem(BaseModel):
    """Skill invocation count."""

    skill: str
    count: int


class MetricsSummaryResponse(BaseModel):
    """Aggregate metrics for a period."""

    period: str
    from_date: datetime
    to_date: datetime
    total_sessions: int
    total_tokens_in: int
    total_tokens_out: int
    total_cost_usd: float
    avg_session_duration_s: float
    autorouter_hit_rate: float
    top_skills: list[SkillUsageItem]


class SkillHeatmapBucket(BaseModel):
    """Skill invocation count for a time bucket."""

    bucket: datetime
    skill: str
    count: int


class SkillHeatmapResponse(BaseModel):
    """Skill usage heatmap data."""

    buckets: list[SkillHeatmapBucket]
    period: str


class PluginMetricsItem(BaseModel):
    """Per-plugin aggregate metrics."""

    plugin: str
    session_count: int
    avg_tokens_in: float
    avg_tokens_out: float
    avg_cost_usd: float
    avg_duration_s: float


class PluginMetricsResponse(BaseModel):
    """Plugin effectiveness comparison data."""

    plugins: list[PluginMetricsItem]
    period: str


class TokenUsageBucket(BaseModel):
    """Token usage for a time bucket."""

    bucket: datetime
    tokens_in: int
    tokens_out: int


class TokenUsageResponse(BaseModel):
    """Token usage over time."""

    buckets: list[TokenUsageBucket]
    period: str


class CostBucket(BaseModel):
    """Cost for a time bucket."""

    bucket: datetime
    cost_usd: float
    session_count: int


class CostResponse(BaseModel):
    """Cost tracking over time."""

    buckets: list[CostBucket]
    total_cost_usd: float
    period: str
