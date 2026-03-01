"""Aggregation queries for telemetry dashboard data.

Uses Python-side processing for JSON field access and time bucketing
so that queries work on both PostgreSQL and SQLite (tests).
"""

import json
from collections import Counter, defaultdict
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.telemetry.models import SessionSummary, TelemetryEvent
from app.telemetry.schemas import (
    CostBucket,
    MetricsPeriod,
    PluginMetricsItem,
    SkillHeatmapBucket,
    SkillUsageItem,
    TokenUsageBucket,
)


def _bucket_key(ts: datetime, period: MetricsPeriod) -> datetime:
    """Truncate a datetime to the start of the given period."""
    if period == MetricsPeriod.DAY:
        return ts.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == MetricsPeriod.WEEK:
        # Monday of the week
        day = ts.replace(hour=0, minute=0, second=0, microsecond=0)
        return day.replace(day=day.day - day.weekday())
    else:  # MONTH
        return ts.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _parse_json_field(value) -> dict | list:
    """Parse a JSON field that may be a string (SQLite) or dict (PostgreSQL)."""
    if isinstance(value, str):
        return json.loads(value)
    return value if value is not None else {}


async def get_metrics_summary(
    db: AsyncSession,
    user_id: str,
    period: MetricsPeriod,
    from_date: datetime,
    to_date: datetime,
) -> dict:
    """Compute aggregate metrics for a user over a time range."""
    stmt = select(
        func.count(SessionSummary.id).label("total_sessions"),
        func.coalesce(func.sum(SessionSummary.total_tokens_in), 0).label(
            "total_tokens_in"
        ),
        func.coalesce(func.sum(SessionSummary.total_tokens_out), 0).label(
            "total_tokens_out"
        ),
        func.coalesce(func.sum(SessionSummary.estimated_cost_usd), 0.0).label(
            "total_cost_usd"
        ),
        func.coalesce(func.avg(SessionSummary.duration_s), 0.0).label(
            "avg_session_duration_s"
        ),
        func.coalesce(func.sum(SessionSummary.autorouter_matches), 0).label(
            "total_matches"
        ),
        func.coalesce(func.sum(SessionSummary.autorouter_misses), 0).label(
            "total_misses"
        ),
    ).where(
        SessionSummary.user_id == user_id,
        SessionSummary.start_time >= from_date,
        SessionSummary.start_time < to_date,
    )

    result = await db.execute(stmt)
    row = result.one()

    total_matches = row.total_matches or 0
    total_misses = row.total_misses or 0
    total_router = total_matches + total_misses
    hit_rate = (total_matches / total_router) if total_router > 0 else 0.0

    top_skills = await _get_top_skills(db, user_id, from_date, to_date, limit=10)

    return {
        "period": period.value,
        "from_date": from_date,
        "to_date": to_date,
        "total_sessions": row.total_sessions,
        "total_tokens_in": row.total_tokens_in,
        "total_tokens_out": row.total_tokens_out,
        "total_cost_usd": float(row.total_cost_usd),
        "avg_session_duration_s": float(row.avg_session_duration_s),
        "autorouter_hit_rate": round(hit_rate, 4),
        "top_skills": top_skills,
    }


async def _get_top_skills(
    db: AsyncSession,
    user_id: str,
    from_date: datetime,
    to_date: datetime,
    limit: int = 10,
) -> list[SkillUsageItem]:
    """Get the most-used skills by loading skill.invoked events."""
    stmt = select(TelemetryEvent.payload).where(
        TelemetryEvent.user_id == user_id,
        TelemetryEvent.event_type == "skill.invoked",
        TelemetryEvent.timestamp >= from_date,
        TelemetryEvent.timestamp < to_date,
    )
    result = await db.execute(stmt)
    counter: Counter[str] = Counter()
    for (payload,) in result.all():
        data = _parse_json_field(payload)
        skill = data.get("skill")
        if skill:
            counter[skill] += 1

    return [
        SkillUsageItem(skill=skill, count=count)
        for skill, count in counter.most_common(limit)
    ]


async def get_skill_heatmap(
    db: AsyncSession,
    user_id: str,
    period: MetricsPeriod,
    from_date: datetime,
    to_date: datetime,
) -> list[SkillHeatmapBucket]:
    """Get skill invocation counts grouped by time bucket."""
    stmt = select(TelemetryEvent.timestamp, TelemetryEvent.payload).where(
        TelemetryEvent.user_id == user_id,
        TelemetryEvent.event_type == "skill.invoked",
        TelemetryEvent.timestamp >= from_date,
        TelemetryEvent.timestamp < to_date,
    )
    result = await db.execute(stmt)

    # Accumulate: (bucket, skill) -> count
    counts: Counter[tuple[datetime, str]] = Counter()
    for ts, payload in result.all():
        data = _parse_json_field(payload)
        skill = data.get("skill", "unknown")
        bucket = _bucket_key(ts, period)
        counts[(bucket, skill)] += 1

    buckets = sorted(counts.keys())
    return [
        SkillHeatmapBucket(bucket=b, skill=s, count=counts[(b, s)]) for b, s in buckets
    ]


async def get_plugin_metrics(
    db: AsyncSession,
    user_id: str,
    from_date: datetime,
    to_date: datetime,
) -> list[PluginMetricsItem]:
    """Compare plugin effectiveness by loading sessions and aggregating."""
    stmt = select(SessionSummary).where(
        SessionSummary.user_id == user_id,
        SessionSummary.start_time >= from_date,
        SessionSummary.start_time < to_date,
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()

    # Accumulate per-plugin metrics
    plugin_data: dict[str, list[SessionSummary]] = defaultdict(list)
    for session in sessions:
        plugins = _parse_json_field(session.plugins_loaded)
        if isinstance(plugins, list):
            for plugin in plugins:
                plugin_data[plugin].append(session)

    items = []
    for plugin, plugin_sessions in sorted(
        plugin_data.items(), key=lambda x: -len(x[1])
    ):
        n = len(plugin_sessions)
        items.append(
            PluginMetricsItem(
                plugin=plugin,
                session_count=n,
                avg_tokens_in=sum(s.total_tokens_in for s in plugin_sessions) / n,
                avg_tokens_out=sum(s.total_tokens_out for s in plugin_sessions) / n,
                avg_cost_usd=sum(s.estimated_cost_usd for s in plugin_sessions) / n,
                avg_duration_s=sum(
                    s.duration_s for s in plugin_sessions if s.duration_s
                )
                / max(1, n),
            )
        )
    return items


async def get_token_usage(
    db: AsyncSession,
    user_id: str,
    period: MetricsPeriod,
    from_date: datetime,
    to_date: datetime,
) -> list[TokenUsageBucket]:
    """Get token usage grouped by time bucket."""
    stmt = select(SessionSummary).where(
        SessionSummary.user_id == user_id,
        SessionSummary.start_time >= from_date,
        SessionSummary.start_time < to_date,
    )
    result = await db.execute(stmt)

    buckets: dict[datetime, tuple[int, int]] = defaultdict(lambda: (0, 0))
    for session in result.scalars().all():
        key = _bucket_key(session.start_time, period)
        tin, tout = buckets[key]
        buckets[key] = (tin + session.total_tokens_in, tout + session.total_tokens_out)

    return [
        TokenUsageBucket(bucket=b, tokens_in=tin, tokens_out=tout)
        for b, (tin, tout) in sorted(buckets.items())
    ]


async def get_cost_over_time(
    db: AsyncSession,
    user_id: str,
    period: MetricsPeriod,
    from_date: datetime,
    to_date: datetime,
) -> list[CostBucket]:
    """Get cost grouped by time bucket."""
    stmt = select(SessionSummary).where(
        SessionSummary.user_id == user_id,
        SessionSummary.start_time >= from_date,
        SessionSummary.start_time < to_date,
    )
    result = await db.execute(stmt)

    buckets: dict[datetime, tuple[float, int]] = defaultdict(lambda: (0.0, 0))
    for session in result.scalars().all():
        key = _bucket_key(session.start_time, period)
        cost, count = buckets[key]
        buckets[key] = (cost + session.estimated_cost_usd, count + 1)

    return [
        CostBucket(bucket=b, cost_usd=cost, session_count=count)
        for b, (cost, count) in sorted(buckets.items())
    ]
