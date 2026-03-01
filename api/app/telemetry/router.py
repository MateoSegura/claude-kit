"""Telemetry ingestion and query endpoints."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import String, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_current_user_flexible, get_db
from app.telemetry.aggregator import (
    get_cost_over_time,
    get_metrics_summary,
    get_plugin_metrics,
    get_skill_heatmap,
    get_token_usage,
)
from app.telemetry.models import SessionSummary, TelemetryEvent
from app.telemetry.schemas import (
    CostResponse,
    EventResponse,
    IngestRequest,
    IngestResponse,
    MetricsPeriod,
    MetricsSummaryResponse,
    PluginMetricsResponse,
    SessionDetailResponse,
    SessionEventsResponse,
    SessionListResponse,
    SessionSummaryResponse,
    SkillHeatmapResponse,
    TokenUsageResponse,
)

router = APIRouter()


def _default_from_date() -> datetime:
    return datetime.now(UTC) - timedelta(days=30)


def _default_to_date() -> datetime:
    return datetime.now(UTC)


# --- Ingest ---


@router.post("/ingest", response_model=IngestResponse, status_code=202)
async def ingest_events(
    body: IngestRequest,
    user: User = Depends(get_current_user_flexible),
    db: AsyncSession = Depends(get_db),
):
    """Accept a batch of telemetry events for storage."""
    events = []
    for event in body.events:
        events.append(
            TelemetryEvent(
                user_id=user.id,
                session_id=body.session_id,
                event_type=event.event_type.value,
                timestamp=event.timestamp,
                payload=event.payload,
            )
        )
    db.add_all(events)

    # Upsert session summary from session.start / session.end events
    await _update_session_summary(db, user.id, body.session_id, body.events)

    await db.flush()
    return IngestResponse(accepted=len(events), session_id=body.session_id)


async def _update_session_summary(
    db: AsyncSession,
    user_id: str,
    session_id: str,
    events: list,
) -> None:
    """Create or update a SessionSummary from session events."""
    result = await db.execute(
        select(SessionSummary).where(SessionSummary.session_id == session_id)
    )
    summary = result.scalar_one_or_none()

    for event in events:
        if event.event_type == "session.start":
            if summary is None:
                summary = SessionSummary(
                    user_id=user_id,
                    session_id=session_id,
                    start_time=event.timestamp,
                    plugins_loaded=event.payload.get("plugins", []),
                )
                db.add(summary)

        elif event.event_type == "session.end":
            if summary is not None:
                summary.end_time = event.timestamp
                summary.duration_s = event.payload.get("duration_s")
                summary.skills_invoked = event.payload.get("skills_invoked", {})
                summary.hooks_fired = event.payload.get("hooks_fired", {})
                summary.autorouter_matches = event.payload.get("autorouter_matches", 0)
                summary.autorouter_misses = event.payload.get("autorouter_misses", 0)


# --- Sessions ---


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    plugin: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Paginated session history for the authenticated user."""
    query = select(SessionSummary).where(SessionSummary.user_id == user.id)
    count_query = select(func.count(SessionSummary.id)).where(
        SessionSummary.user_id == user.id
    )

    if from_date:
        query = query.where(SessionSummary.start_time >= from_date)
        count_query = count_query.where(SessionSummary.start_time >= from_date)
    if to_date:
        query = query.where(SessionSummary.start_time < to_date)
        count_query = count_query.where(SessionSummary.start_time < to_date)
    if plugin:
        # Use cast+like for SQLite compatibility (no JSONB containment)
        json_str = cast(SessionSummary.plugins_loaded, String)
        query = query.where(json_str.contains(f'"{plugin}"'))
        count_query = count_query.where(json_str.contains(f'"{plugin}"'))

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * per_page
    query = (
        query.order_by(SessionSummary.start_time.desc()).offset(offset).limit(per_page)
    )
    result = await db.execute(query)
    sessions = result.scalars().all()

    return SessionListResponse(
        sessions=[SessionSummaryResponse.model_validate(s) for s in sessions],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detail for a single session."""
    result = await db.execute(
        select(SessionSummary).where(
            SessionSummary.session_id == session_id,
            SessionSummary.user_id == user.id,
        )
    )
    summary = result.scalar_one_or_none()
    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    event_count_result = await db.execute(
        select(func.count(TelemetryEvent.id)).where(
            TelemetryEvent.session_id == session_id,
            TelemetryEvent.user_id == user.id,
        )
    )
    event_count = event_count_result.scalar_one()

    data = SessionSummaryResponse.model_validate(summary).model_dump()
    data["event_count"] = event_count
    return SessionDetailResponse(**data)


@router.get("/sessions/{session_id}/events", response_model=SessionEventsResponse)
async def get_session_events(
    session_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated events for a session."""
    # Verify session belongs to user
    session_check = await db.execute(
        select(SessionSummary.id).where(
            SessionSummary.session_id == session_id,
            SessionSummary.user_id == user.id,
        )
    )
    if session_check.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    count_result = await db.execute(
        select(func.count(TelemetryEvent.id)).where(
            TelemetryEvent.session_id == session_id,
            TelemetryEvent.user_id == user.id,
        )
    )
    total = count_result.scalar_one()

    offset = (page - 1) * per_page
    result = await db.execute(
        select(TelemetryEvent)
        .where(
            TelemetryEvent.session_id == session_id,
            TelemetryEvent.user_id == user.id,
        )
        .order_by(TelemetryEvent.timestamp)
        .offset(offset)
        .limit(per_page)
    )
    events = result.scalars().all()

    return SessionEventsResponse(
        events=[EventResponse.model_validate(e) for e in events],
        total=total,
        page=page,
        per_page=per_page,
    )


# --- Metrics ---


@router.get("/metrics/summary", response_model=MetricsSummaryResponse)
async def metrics_summary(
    period: MetricsPeriod = MetricsPeriod.WEEK,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate metrics for the authenticated user."""
    fd = from_date or _default_from_date()
    td = to_date or _default_to_date()
    data = await get_metrics_summary(db, user.id, period, fd, td)
    return MetricsSummaryResponse(**data)


@router.get("/metrics/skills", response_model=SkillHeatmapResponse)
async def metrics_skills(
    period: MetricsPeriod = MetricsPeriod.DAY,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Skill usage heatmap data."""
    fd = from_date or _default_from_date()
    td = to_date or _default_to_date()
    buckets = await get_skill_heatmap(db, user.id, period, fd, td)
    return SkillHeatmapResponse(buckets=buckets, period=period.value)


@router.get("/metrics/plugins", response_model=PluginMetricsResponse)
async def metrics_plugins(
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Plugin effectiveness comparison data."""
    fd = from_date or _default_from_date()
    td = to_date or _default_to_date()
    period = MetricsPeriod.MONTH
    plugins = await get_plugin_metrics(db, user.id, fd, td)
    return PluginMetricsResponse(plugins=plugins, period=period.value)


@router.get("/metrics/tokens", response_model=TokenUsageResponse)
async def metrics_tokens(
    period: MetricsPeriod = MetricsPeriod.DAY,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Token usage over time."""
    fd = from_date or _default_from_date()
    td = to_date or _default_to_date()
    buckets = await get_token_usage(db, user.id, period, fd, td)
    return TokenUsageResponse(buckets=buckets, period=period.value)


@router.get("/metrics/cost", response_model=CostResponse)
async def metrics_cost(
    period: MetricsPeriod = MetricsPeriod.DAY,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cost tracking over time."""
    fd = from_date or _default_from_date()
    td = to_date or _default_to_date()
    buckets = await get_cost_over_time(db, user.id, period, fd, td)
    total = sum(b.cost_usd for b in buckets)
    return CostResponse(buckets=buckets, total_cost_usd=total, period=period.value)
