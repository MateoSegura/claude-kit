# claude-kit API

FastAPI service providing telemetry ingestion, session queries, and dashboard
data for claude-kit sessions.

## Quick Start

```bash
cd api
pip install -r requirements.txt
uvicorn app.main:app --factory --reload
```

The API starts on `http://localhost:8000`. Health check: `GET /healthz`

## Authentication

The API supports two authentication methods:

**JWT Bearer tokens** — for dashboard and interactive use:
```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword123"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword123"}'
```

**API keys** — for CLI telemetry upload:
```bash
# Create an API key (requires JWT auth)
curl -X POST http://localhost:8000/api/v1/auth/api-keys \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-cli-key"}'

# Use the API key
curl -X POST http://localhost:8000/api/v1/telemetry/ingest \
  -H "X-API-Key: ck_live_..." \
  -H "Content-Type: application/json" \
  -d '{"session_id": "...", "events": [...]}'
```

## Telemetry Endpoints

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

See `docs/specs/telemetry-and-testing-2026-03-01/dashboard-data-contract.md`
for full request/response schemas.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./telemetry.db` | Database connection string |
| `JWT_SECRET` | (required) | Secret key for JWT signing |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `GITHUB_CLIENT_ID` | — | GitHub OAuth app ID |
| `GITHUB_CLIENT_SECRET` | — | GitHub OAuth app secret |
| `GOOGLE_CLIENT_ID` | — | Google OAuth app ID |
| `GOOGLE_CLIENT_SECRET` | — | Google OAuth app secret |

## Running Tests

```bash
cd api
pip install -r requirements.txt
pytest -v
```

Tests use SQLite in-memory for speed. No external services required.

## Project Structure

```
api/
├── app/
│   ├── main.py              # FastAPI app factory
│   ├── config.py            # Pydantic settings
│   ├── dependencies.py      # DI: DB sessions, auth
│   ├── models/
│   │   └── base.py          # SQLAlchemy declarative base
│   ├── auth/
│   │   ├── models.py        # User, RefreshToken, APIKey, OAuthConnection
│   │   ├── router.py        # Auth endpoints
│   │   ├── jwt.py           # Token creation/validation
│   │   └── oauth.py         # OAuth provider integration
│   └── telemetry/
│       ├── models.py         # TelemetryEvent, SessionSummary
│       ├── schemas.py        # Pydantic request/response models
│       ├── router.py         # Telemetry endpoints
│       └── aggregator.py     # Dashboard aggregation queries
├── tests/
│   ├── conftest.py           # Async fixtures, SQLite test DB
│   ├── test_auth.py          # Auth endpoint tests
│   ├── test_telemetry.py     # Telemetry endpoint unit tests
│   └── test_integration.py   # Full-pipeline integration tests
├── requirements.txt
└── pyproject.toml
```
