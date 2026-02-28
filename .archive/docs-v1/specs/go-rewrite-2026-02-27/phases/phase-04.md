# Phase 04: Telemetry & Conversation Pipeline

## Objective

Build the client-side telemetry collector (in the CLI) and server-side ingestion pipeline so that usage events, error reports, and conversation logs flow from CLI sessions to the backend for storage, analysis, and dashboard display.

## Satisfies

- R10: Client-side telemetry — plugin loads, commands, compactions, session duration, model, OS/arch
- R11: Error/crash reporting — panics captured with context, uploaded with opt-in consent
- R12: Conversation capture — session logs uploaded for history and replay

## Steps

1. [ ] Implement telemetry collector — `internal/telemetry/collector.go` with `Track(event, properties)` that buffers events in memory and flushes on interval or session end
2. [ ] Implement offline queue — `internal/telemetry/queue.go` using SQLite (`~/.config/claude-kit/telemetry.db`) to persist events when offline; drain queue when connectivity returns
3. [ ] Implement telemetry uploader — `internal/telemetry/uploader.go` with batched POST to `/telemetry/events`, retry with exponential backoff, circuit breaker on repeated failures
4. [ ] Implement crash reporter — `internal/telemetry/crash.go` with `recover()` wrapper that captures panic stack traces, sanitizes secrets (API keys, file paths with usernames), and uploads to `/telemetry/crashes`
5. [ ] Implement opt-in consent — first-run prompt: "claude-kit collects anonymous usage data to improve the product. You can disable this anytime with `claude-kit telemetry off`. Enable telemetry?" Store choice in `~/.config/claude-kit/config.json`
6. [ ] Implement conversation capture — during `--kit` sessions, optionally capture Claude's stdout/stderr to a local file; on session end, upload compressed log to `/conversations/upload`
7. [ ] Add telemetry ingestion endpoints — `apps/backend/routes/telemetry.go` with `POST /telemetry/events` (batch), `POST /telemetry/crashes`, `GET /telemetry/events` (query with filters)
8. [ ] Add conversation endpoints — `apps/backend/routes/conversations.go` with `POST /conversations/upload` (multipart), `GET /conversations` (list), `GET /conversations/{id}` (download), `DELETE /conversations/{id}`
9. [ ] Create ent schema entities — `ent/schema/telemetryevent.go`, `ent/schema/crashreport.go`, `ent/schema/conversation.go` and regenerate the ent client
10. [ ] Implement S3-compatible storage — `internal/storage/s3.go` for conversation log upload/download (MinIO in dev, any S3-compatible in prod)
11. [ ] Implement telemetry aggregation — background worker that rolls up raw events into per-user daily/weekly summaries (for dashboard analytics)
12. [ ] Wire telemetry into CLI commands — `cmd/run.go` tracks session start/end, plugin loads, model selection; `cmd/validate.go` tracks validation runs
13. [ ] Add `claude-kit telemetry` subcommand — `on`/`off`/`status` to control telemetry; `export` to download all your data; `delete` to request data deletion
14. [ ] Write integration tests — test event ingestion, offline queue drain, crash report upload, conversation upload/download

## Files to Create/Modify

### Create
- `internal/telemetry/collector.go` — event buffering, flush logic
- `internal/telemetry/queue.go` — SQLite offline queue
- `internal/telemetry/uploader.go` — batched upload with retry
- `internal/telemetry/crash.go` — panic recovery + sanitization
- `internal/telemetry/consent.go` — opt-in flow, config read/write
- `internal/telemetry/telemetry_test.go` — unit tests
- `internal/storage/s3.go` — S3-compatible object storage client
- `internal/storage/storage_test.go` — storage tests (using MinIO testcontainer)
- `apps/backend/routes/telemetry.go` — event/crash ingestion endpoints
- `apps/backend/routes/conversations.go` — conversation upload/download/list
- `apps/backend/workers/aggregator.go` — background telemetry rollup worker
- `apps/cli/cmd/telemetry.go` — `telemetry on/off/status/export/delete` subcommand
- `ent/schema/telemetryevent.go` — TelemetryEvent entity (fields, indexes, edges to User/Session)
- `ent/schema/crashreport.go` — CrashReport entity (fields, edges to User)
- `ent/schema/conversation.go` — Conversation entity (fields, edges to User/Session, S3 storage key)

### Modify
- `apps/cli/cmd/run.go` — add telemetry hooks (session start, plugin loads, session end)
- `apps/cli/cmd/root.go` — wrap `Execute()` in crash reporter, initialize telemetry collector
- `apps/cli/cmd/validate.go` — track validation events
- `internal/config/cli.go` — add telemetry config paths
- `deploy/backend/docker-compose.yml` — add MinIO service for local S3

## Event Schema

```json
{
  "event_id": "uuid",
  "user_id": "uuid",
  "session_id": "uuid",
  "event_type": "session.start | session.end | plugin.load | command.run | compact.trigger | error.unhandled",
  "properties": {
    "kit_name": "embedded-zephyr-engineer",
    "plugins_loaded": ["embedded-zephyr-engineer", "core-kit", "core-spec"],
    "model": "opus",
    "os": "darwin/arm64",
    "cli_version": "v1.0.0",
    "duration_secs": 3600,
    "compact_count": 2
  },
  "timestamp": "2026-02-27T10:30:00Z"
}
```

## Crash Report Schema

```json
{
  "crash_id": "uuid",
  "user_id": "uuid",
  "session_id": "uuid",
  "cli_version": "v1.0.0",
  "os": "darwin/arm64",
  "go_version": "go1.23.0",
  "stack_trace": "[sanitized stack trace]",
  "error_message": "[sanitized error message]",
  "context": {
    "command": "run",
    "kit": "embedded-zephyr-engineer",
    "plugins_loaded": 5
  },
  "timestamp": "2026-02-27T10:30:00Z"
}
```

## ent Schema Definitions

```go
// ent/schema/telemetryevent.go
func (TelemetryEvent) Fields() []ent.Field {
    return []ent.Field{
        field.UUID("id", uuid.UUID{}).Default(uuid.New),
        field.String("event_type").NotEmpty(),
        field.JSON("properties", map[string]any{}).Optional(),
        field.Time("created_at").Default(time.Now),
    }
}
func (TelemetryEvent) Edges() []ent.Edge {
    return []ent.Edge{
        edge.From("user", User.Type).Ref("telemetry_events").Unique().Required(),
        edge.From("session", Session.Type).Ref("telemetry_events").Unique().Optional(),
    }
}
func (TelemetryEvent) Indexes() []ent.Index {
    return []ent.Index{
        index.Fields("created_at").Edges("user"),
        index.Edges("session"),
        index.Fields("event_type"),
    }
}

// ent/schema/crashreport.go
func (CrashReport) Fields() []ent.Field {
    return []ent.Field{
        field.UUID("id", uuid.UUID{}).Default(uuid.New),
        field.String("cli_version").NotEmpty(),
        field.String("os").NotEmpty(),
        field.String("go_version").NotEmpty(),
        field.Text("stack_trace").NotEmpty(),
        field.Text("error_message").NotEmpty(),
        field.JSON("context", map[string]any{}).Optional(),
        field.Time("created_at").Default(time.Now),
    }
}

// ent/schema/conversation.go
func (Conversation) Fields() []ent.Field {
    return []ent.Field{
        field.UUID("id", uuid.UUID{}).Default(uuid.New),
        field.String("storage_key").NotEmpty(),      // S3 object key
        field.Int64("size_bytes"),
        field.Int("duration_secs").Optional(),
        field.Int("compact_count").Default(0),
        field.Strings("plugins_loaded").Optional(),
        field.String("model").Optional(),
        field.Time("created_at").Default(time.Now),
    }
}
```

## API Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/telemetry/events` | API key | Batch ingest events |
| POST | `/telemetry/crashes` | API key | Upload crash report |
| GET | `/telemetry/events` | JWT | Query events (with filters) |
| GET | `/telemetry/summary` | JWT | Aggregated usage summary |
| POST | `/conversations/upload` | API key | Upload conversation log |
| GET | `/conversations` | JWT | List conversations |
| GET | `/conversations/{id}` | JWT | Download conversation |
| DELETE | `/conversations/{id}` | JWT | Delete conversation |
| POST | `/telemetry/export` | JWT | Export all user data |
| POST | `/telemetry/delete` | JWT | Request data deletion |

## Acceptance Criteria

- [ ] `claude-kit --kit <name>` automatically sends `session.start`, `plugin.load`, and `session.end` events to the backend
- [ ] When offline, events queue in SQLite and drain automatically when connectivity returns (verified by disconnecting network during a session)
- [ ] Crash reports are captured on unhandled panics and uploaded on next CLI invocation
- [ ] Crash reports contain no secrets — API keys, user home paths, and credentials are sanitized
- [ ] `claude-kit telemetry off` stops all data collection; `claude-kit telemetry on` resumes
- [ ] `claude-kit telemetry status` shows current opt-in state and queue size
- [ ] `claude-kit telemetry export` downloads all user telemetry data as JSON
- [ ] Conversation logs are compressed (gzip) before upload and stored in S3
- [ ] `GET /telemetry/summary` returns per-day aggregated usage data for the last 90 days
- [ ] Telemetry ingestion handles 1000 events/second per user without dropping data

## Dependencies

- Requires: Phase 03 (needs API server, auth middleware, database)
- Blocks: Phase 06 (dashboard displays telemetry data)
