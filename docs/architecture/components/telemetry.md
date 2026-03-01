# Telemetry Architecture

**Status:** active
**Date:** 2026-03-01

## Overview

claude-kit includes an opt-in telemetry system that captures structured session
events during Claude Code sessions. Events flow through a local pipeline first,
with an optional HTTP upload path to a centralized API for dashboard queries.

## Data Flow

```
Claude Code session
       │
       ▼
TelemetryEmitter (in claude-kit CLI)
       │
       ├──► Local JSONL file (~/.claude-kit/telemetry/<session-id>.jsonl)
       │
       └──► HTTP POST to API (optional, requires CLAUDE_KIT_TELEMETRY=full)
                │
                ▼
        /api/v1/telemetry/ingest
                │
                ├──► TelemetryEvent table (raw events)
                └──► SessionSummary table (aggregated per session)
                          │
                          ▼
                Dashboard query endpoints
                (sessions, metrics, skills, plugins, tokens, cost)
```

## Event Schema (v1)

Every event is a JSON object with these required fields:

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | int | Always `1` |
| `event_type` | string | One of 8 defined types |
| `timestamp` | ISO 8601 | When the event occurred |
| `session_id` | UUID string | Groups events into sessions |
| `payload` | object | Type-specific data |

### Event Types

| Type | Emitted when | Key payload fields |
|------|-------------|-------------------|
| `session.start` | Session begins | `plugins`, `mode`, `telemetry_level` |
| `session.end` | Session closes | `duration_s`, `skills_invoked`, `hooks_fired`, `autorouter_matches` |
| `plugin.loaded` | Plugin activated | `plugin`, `role`, `domain` |
| `skill.invoked` | Skill used | `skill`, `trigger` |
| `hook.fired` | Hook executed | `event`, `hook_type`, `result` |
| `autorouter.match` | Intent matched | `intent`, `matched_skill` |
| `autorouter.miss` | No match found | `intent` |
| `validation.result` | Validation ran | `validator`, `passed`, `errors` |

## Configuration

Telemetry behavior is controlled by environment variables:

| Variable | Values | Default | Purpose |
|----------|--------|---------|---------|
| `CLAUDE_KIT_TELEMETRY` | `off`, `debug`, `local`, `full` | `off` | Controls telemetry level |
| `CLAUDE_KIT_API_URL` | URL string | — | API service base URL |
| `CLAUDE_KIT_API_KEY` | API key string | — | Authentication for upload |

### Telemetry Levels

| Level | Local JSONL | Debug traces | API upload |
|-------|------------|-------------|------------|
| `off` | No | No | No |
| `debug` | No | Yes (stderr) | No |
| `local` | Yes | Yes | No |
| `full` | Yes | Yes | Yes (if API configured) |

API upload only occurs when all three conditions are met:
1. `CLAUDE_KIT_TELEMETRY=full`
2. `CLAUDE_KIT_API_URL` is set to a valid URL
3. `CLAUDE_KIT_API_KEY` is set to a valid API key

If any condition is missing, upload silently skips — no error, no warning.

## API Architecture

The telemetry API is a FastAPI service in `api/` with:
- **SQLAlchemy 2.0 async** ORM with PostgreSQL (production) or SQLite (tests)
- **Dual auth**: JWT Bearer tokens for dashboard access, API keys for CLI upload
- **Python-side aggregation** for cross-database compatibility

### Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/v1/telemetry/ingest` | JWT or API Key | Batch event ingestion |
| GET | `/api/v1/telemetry/sessions` | JWT | Paginated session list |
| GET | `/api/v1/telemetry/sessions/{id}` | JWT | Session detail |
| GET | `/api/v1/telemetry/sessions/{id}/events` | JWT | Session event timeline |
| GET | `/api/v1/telemetry/metrics/summary` | JWT | Aggregate KPIs |
| GET | `/api/v1/telemetry/metrics/skills` | JWT | Skill usage heatmap |
| GET | `/api/v1/telemetry/metrics/plugins` | JWT | Plugin comparison |
| GET | `/api/v1/telemetry/metrics/tokens` | JWT | Token usage over time |
| GET | `/api/v1/telemetry/metrics/cost` | JWT | Cost tracking |

## Design Decisions

- **Opt-in only (AD-5)**: No data leaves the machine without explicit configuration
- **Graceful degradation**: Upload failures log to stderr and never crash the CLI
- **Stdlib HTTP**: Upload uses `http.client` — no third-party dependencies in the CLI
- **Local-first**: JSONL files are always written (at `local`+ level) regardless of API availability
- **Forward-compatible**: `flush_buffer()` returns raw event dicts for use by a future Python library

## Traces

- ADR-005 (glass-box transparency) — telemetry extends the transparency model
- SPEC: `docs/specs/telemetry-and-testing-2026-03-01/`
