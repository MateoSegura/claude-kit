"""Telemetry ingestion and query endpoint tests."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Register a user and return auth headers."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "telemetry@example.com",
            "password": "securepassword123",
            "display_name": "Telemetry User",
        },
    )
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def api_key_headers(client: AsyncClient, auth_headers: dict) -> dict[str, str]:
    """Create an API key and return headers using it."""
    resp = await client.post(
        "/api/v1/auth/api-keys",
        json={"name": "telemetry-cli", "is_test": False},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    raw_key = resp.json()["raw_key"]
    return {"X-API-Key": raw_key}


def _make_events(
    session_id: str = "test-session-001",
    start_offset_hours: int = 0,
) -> dict:
    """Build a valid ingest request body with session start + end + some events."""
    base_time = datetime.now(UTC) - timedelta(hours=start_offset_hours)
    return {
        "session_id": session_id,
        "events": [
            {
                "event_type": "session.start",
                "timestamp": base_time.isoformat(),
                "payload": {
                    "plugins": ["core-kit", "cloud-python-engineer"],
                    "mode": "dev",
                    "telemetry_level": "full",
                },
            },
            {
                "event_type": "plugin.loaded",
                "timestamp": (base_time + timedelta(seconds=1)).isoformat(),
                "payload": {
                    "plugin": "core-kit",
                    "role": "system",
                    "domain": "universal",
                },
            },
            {
                "event_type": "plugin.loaded",
                "timestamp": (base_time + timedelta(seconds=2)).isoformat(),
                "payload": {
                    "plugin": "cloud-python-engineer",
                    "role": "engineer",
                    "domain": "backend",
                },
            },
            {
                "event_type": "prompt.submitted",
                "timestamp": (base_time + timedelta(seconds=10)).isoformat(),
                "payload": {
                    "prompt": "build a REST API",
                    "turn": 1,
                },
            },
            {
                "event_type": "skill.invoked",
                "timestamp": (base_time + timedelta(seconds=30)).isoformat(),
                "payload": {"skill": "core-kit:routing", "trigger": "autoroute"},
            },
            {
                "event_type": "skill.invoked",
                "timestamp": (base_time + timedelta(seconds=60)).isoformat(),
                "payload": {
                    "skill": "cloud-python-engineer:engineer",
                    "trigger": "explicit",
                },
            },
            {
                "event_type": "autorouter.match",
                "timestamp": (base_time + timedelta(seconds=30)).isoformat(),
                "payload": {
                    "intent": "build a service",
                    "matched_skill": "core-kit:routing",
                },
            },
            {
                "event_type": "tool.used",
                "timestamp": (base_time + timedelta(seconds=40)).isoformat(),
                "payload": {
                    "tool_name": "Read",
                    "tool_use_id": "tu-1",
                    "is_mcp": False,
                },
            },
            {
                "event_type": "tool.result",
                "timestamp": (base_time + timedelta(seconds=41)).isoformat(),
                "payload": {
                    "tool_use_id": "tu-1",
                    "is_error": False,
                    "content_preview": "file contents",
                },
            },
            {
                "event_type": "tool.used",
                "timestamp": (base_time + timedelta(seconds=50)).isoformat(),
                "payload": {
                    "tool_name": "mcp__github__get_issue",
                    "tool_use_id": "tu-2",
                    "is_mcp": True,
                    "mcp_server": "github",
                    "mcp_method": "get_issue",
                },
            },
            {
                "event_type": "turn.completed",
                "timestamp": (base_time + timedelta(seconds=55)).isoformat(),
                "payload": {
                    "turn": 1,
                    "model": "claude-haiku-4-5-20251001",
                    "content_types": ["text", "tool_use"],
                    "tool_calls": ["Read", "mcp__github__get_issue"],
                    "mcp_calls": ["mcp__github__get_issue"],
                },
            },
            {
                "event_type": "message.assistant",
                "timestamp": (base_time + timedelta(seconds=56)).isoformat(),
                "payload": {
                    "model": "claude-haiku-4-5-20251001",
                    "text": "Here is the result",
                    "content_types": ["text"],
                },
            },
            {
                "event_type": "session.result",
                "timestamp": (base_time + timedelta(seconds=119)).isoformat(),
                "payload": {
                    "usage": {"input_tokens": 500, "output_tokens": 200},
                    "duration_ms": 120000,
                    "duration_api_ms": 100000,
                    "session_id": "sdk-session-001",
                    "cost_usd": 0.005,
                    "num_turns": 3,
                    "is_error": False,
                },
            },
            {
                "event_type": "session.end",
                "timestamp": (base_time + timedelta(seconds=120)).isoformat(),
                "payload": {
                    "duration_s": 120.0,
                    "plugins_loaded": 2,
                    "skills_invoked": {
                        "core-kit:routing": 1,
                        "cloud-python-engineer:engineer": 1,
                    },
                    "hooks_fired": {"PreToolUse": 3},
                    "autorouter_matches": 1,
                    "autorouter_misses": 0,
                    "tool_uses": {"Read": 1, "mcp__github__get_issue": 1},
                    "mcp_calls": {"github": 1},
                    "compact_count": 0,
                    "total_tokens_in": 500,
                    "total_tokens_out": 200,
                    "cost_usd": 0.005,
                    "model": "claude-haiku-4-5-20251001",
                    "total_turns": 3,
                },
            },
        ],
    }


class TestIngest:
    """Telemetry ingest endpoint tests."""

    async def test_ingest_with_jwt(self, client: AsyncClient, auth_headers: dict):
        body = _make_events()
        resp = await client.post(
            "/api/v1/telemetry/ingest",
            json=body,
            headers=auth_headers,
        )
        assert resp.status_code == 202
        data = resp.json()
        assert data["accepted"] == 14
        assert data["session_id"] == "test-session-001"

    async def test_ingest_with_api_key(
        self, client: AsyncClient, api_key_headers: dict
    ):
        body = _make_events(session_id="api-key-session")
        resp = await client.post(
            "/api/v1/telemetry/ingest",
            json=body,
            headers=api_key_headers,
        )
        assert resp.status_code == 202
        assert resp.json()["accepted"] == 14

    async def test_ingest_without_auth(self, client: AsyncClient):
        body = _make_events()
        resp = await client.post("/api/v1/telemetry/ingest", json=body)
        assert resp.status_code == 401

    async def test_ingest_invalid_event_type(
        self, client: AsyncClient, auth_headers: dict
    ):
        body = {
            "session_id": "bad-session",
            "events": [
                {
                    "event_type": "invalid.type",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "payload": {},
                }
            ],
        }
        resp = await client.post(
            "/api/v1/telemetry/ingest",
            json=body,
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_ingest_empty_events(self, client: AsyncClient, auth_headers: dict):
        body = {"session_id": "empty-session", "events": []}
        resp = await client.post(
            "/api/v1/telemetry/ingest",
            json=body,
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestSessions:
    """Session query endpoint tests."""

    async def test_list_sessions_empty(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/telemetry/sessions", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["sessions"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    async def test_list_sessions_with_data(
        self, client: AsyncClient, auth_headers: dict
    ):
        # Ingest a session first
        await client.post(
            "/api/v1/telemetry/ingest",
            json=_make_events(),
            headers=auth_headers,
        )

        resp = await client.get("/api/v1/telemetry/sessions", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["sessions"]) == 1
        session = data["sessions"][0]
        assert session["session_id"] == "test-session-001"
        assert session["duration_s"] == 120.0
        assert session["autorouter_matches"] == 1

    async def test_session_detail(self, client: AsyncClient, auth_headers: dict):
        await client.post(
            "/api/v1/telemetry/ingest",
            json=_make_events(),
            headers=auth_headers,
        )

        resp = await client.get(
            "/api/v1/telemetry/sessions/test-session-001",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == "test-session-001"
        assert data["event_count"] == 14

    async def test_session_detail_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        resp = await client.get(
            "/api/v1/telemetry/sessions/nonexistent",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_session_events(self, client: AsyncClient, auth_headers: dict):
        await client.post(
            "/api/v1/telemetry/ingest",
            json=_make_events(),
            headers=auth_headers,
        )

        resp = await client.get(
            "/api/v1/telemetry/sessions/test-session-001/events",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 14
        assert len(data["events"]) == 14
        # Events should be ordered by timestamp
        types = [e["event_type"] for e in data["events"]]
        assert types[0] == "session.start"
        assert types[-1] == "session.end"

    async def test_session_events_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        resp = await client.get(
            "/api/v1/telemetry/sessions/nonexistent/events",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_session_summary_includes_new_fields(
        self, client: AsyncClient, auth_headers: dict
    ):
        await client.post(
            "/api/v1/telemetry/ingest",
            json=_make_events(),
            headers=auth_headers,
        )

        resp = await client.get(
            "/api/v1/telemetry/sessions/test-session-001",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["tool_uses"] == {"Read": 1, "mcp__github__get_issue": 1}
        assert data["mcp_calls"] == {"github": 1}
        assert data["compact_count"] == 0
        assert data["model"] == "claude-haiku-4-5-20251001"
        assert data["cost_usd"] == 0.005
        assert data["total_turns"] == 3
        assert data["total_tokens_in"] == 500
        assert data["total_tokens_out"] == 200

    async def test_sessions_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/api/v1/telemetry/sessions")
        assert resp.status_code == 401


class TestMetrics:
    """Metrics query endpoint tests."""

    async def test_summary_empty(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get(
            "/api/v1/telemetry/metrics/summary", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_sessions"] == 0
        assert data["total_tokens_in"] == 0
        assert data["autorouter_hit_rate"] == 0.0

    async def test_summary_with_data(self, client: AsyncClient, auth_headers: dict):
        await client.post(
            "/api/v1/telemetry/ingest",
            json=_make_events(),
            headers=auth_headers,
        )

        resp = await client.get(
            "/api/v1/telemetry/metrics/summary",
            params={"period": "month"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_sessions"] == 1
        assert data["period"] == "month"

    async def test_skills_empty(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get(
            "/api/v1/telemetry/metrics/skills", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["buckets"] == []

    async def test_plugins_empty(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get(
            "/api/v1/telemetry/metrics/plugins", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["plugins"] == []

    async def test_tokens_empty(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get(
            "/api/v1/telemetry/metrics/tokens", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["buckets"] == []

    async def test_cost_empty(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/telemetry/metrics/cost", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["buckets"] == []
        assert data["total_cost_usd"] == 0.0

    async def test_metrics_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/api/v1/telemetry/metrics/summary")
        assert resp.status_code == 401


class TestEventStream:
    """Event stream endpoint tests."""

    async def test_stream_all_events(self, client: AsyncClient, auth_headers: dict):
        """First call without 'after' returns all events."""
        await client.post(
            "/api/v1/telemetry/ingest",
            json=_make_events(),
            headers=auth_headers,
        )

        resp = await client.get(
            "/api/v1/telemetry/sessions/test-session-001/events/stream",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 14
        assert len(data["events"]) == 14
        assert data["page"] == 1
        assert data["per_page"] == 1000
        # Events should be ordered by timestamp
        types = [e["event_type"] for e in data["events"]]
        assert types[0] == "session.start"
        assert types[-1] == "session.end"

    async def test_stream_with_after(self, client: AsyncClient, auth_headers: dict):
        """Passing 'after' returns only events after that timestamp."""
        await client.post(
            "/api/v1/telemetry/ingest",
            json=_make_events(),
            headers=auth_headers,
        )

        # Get all events to find a midpoint timestamp
        all_resp = await client.get(
            "/api/v1/telemetry/sessions/test-session-001/events/stream",
            headers=auth_headers,
        )
        all_events = all_resp.json()["events"]
        midpoint_ts = all_events[5]["timestamp"]

        # Now stream with after=midpoint
        resp = await client.get(
            "/api/v1/telemetry/sessions/test-session-001/events/stream",
            params={"after": midpoint_ts},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # Should return fewer events (only those after the midpoint)
        assert len(data["events"]) < 14
        assert len(data["events"]) > 0
        # Total should still reflect all session events
        assert data["total"] == 14

    async def test_stream_not_found(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get(
            "/api/v1/telemetry/sessions/nonexistent/events/stream",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_stream_prompt_submitted_event(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Verify prompt.submitted event type is accepted and returned."""
        await client.post(
            "/api/v1/telemetry/ingest",
            json=_make_events(),
            headers=auth_headers,
        )

        resp = await client.get(
            "/api/v1/telemetry/sessions/test-session-001/events/stream",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        types = [e["event_type"] for e in resp.json()["events"]]
        assert "prompt.submitted" in types
