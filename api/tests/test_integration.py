"""Full-pipeline integration tests: register → ingest → query → metrics.

Exercises the complete telemetry data flow in a single test session,
verifying that data ingested via the CLI upload path is queryable through
all dashboard endpoints with correct aggregation.
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient


@pytest.fixture
async def user_session(client: AsyncClient) -> dict[str, str | dict]:
    """Register a user, create an API key, and return both auth headers."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "integration@example.com",
            "password": "securepassword123",
            "display_name": "Integration Tester",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    jwt_headers = {"Authorization": f"Bearer {token}"}

    key_resp = await client.post(
        "/api/v1/auth/api-keys",
        json={"name": "integration-cli", "is_test": False},
        headers=jwt_headers,
    )
    assert key_resp.status_code == 201
    api_key_headers = {"X-API-Key": key_resp.json()["raw_key"]}

    return {
        "jwt_headers": jwt_headers,
        "api_key_headers": api_key_headers,
    }


def _build_session_events(
    session_id: str,
    base_time: datetime,
    duration_s: float = 180.0,
    plugins: list[str] | None = None,
    skills: dict[str, int] | None = None,
) -> dict:
    """Build a realistic session event batch for integration testing.

    Returns a dict ready to POST to /api/v1/telemetry/ingest.
    This helper is intentionally reusable so a future Python library
    test can call it directly without HTTP overhead.
    """
    plugins = plugins or ["core-kit", "cloud-python-engineer"]
    skills = skills or {"core-kit:routing": 2, "cloud-python-engineer:engineer": 1}

    events = [
        {
            "event_type": "session.start",
            "timestamp": base_time.isoformat(),
            "payload": {
                "plugins": plugins,
                "mode": "dev",
                "telemetry_level": "full",
            },
        },
    ]

    # Plugin loaded events
    offset = 1
    for plugin in plugins:
        events.append(
            {
                "event_type": "plugin.loaded",
                "timestamp": (base_time + timedelta(seconds=offset)).isoformat(),
                "payload": {"plugin": plugin, "role": "system", "domain": "backend"},
            }
        )
        offset += 1

    # Skill invocations
    for skill, count in skills.items():
        for i in range(count):
            events.append(
                {
                    "event_type": "skill.invoked",
                    "timestamp": (
                        base_time + timedelta(seconds=offset + i * 10)
                    ).isoformat(),
                    "payload": {"skill": skill, "trigger": "autoroute"},
                }
            )
        offset += count * 10

    # Autorouter events
    events.append(
        {
            "event_type": "autorouter.match",
            "timestamp": (base_time + timedelta(seconds=offset)).isoformat(),
            "payload": {
                "intent": "build a service",
                "matched_skill": "core-kit:routing",
            },
        }
    )
    events.append(
        {
            "event_type": "autorouter.miss",
            "timestamp": (base_time + timedelta(seconds=offset + 1)).isoformat(),
            "payload": {"intent": "something unknown"},
        }
    )

    # Session end
    events.append(
        {
            "event_type": "session.end",
            "timestamp": (base_time + timedelta(seconds=duration_s)).isoformat(),
            "payload": {
                "duration_s": duration_s,
                "plugins_loaded": len(plugins),
                "skills_invoked": skills,
                "hooks_fired": {"PreToolUse": 5, "PostToolUse": 2},
                "autorouter_matches": 1,
                "autorouter_misses": 1,
            },
        }
    )

    return {"session_id": session_id, "events": events}


class TestFullPipeline:
    """End-to-end: ingest with API key, query with JWT, verify metrics."""

    async def test_ingest_then_query_sessions(
        self, client: AsyncClient, user_session: dict
    ):
        """Ingest a session via API key, then query it via JWT."""
        base_time = datetime.now(UTC) - timedelta(hours=1)
        body = _build_session_events("integration-001", base_time)

        # Ingest with API key (simulates CLI upload)
        ingest = await client.post(
            "/api/v1/telemetry/ingest",
            json=body,
            headers=user_session["api_key_headers"],
        )
        assert ingest.status_code == 202
        assert ingest.json()["accepted"] == len(body["events"])

        # Query sessions with JWT (simulates dashboard)
        sessions = await client.get(
            "/api/v1/telemetry/sessions",
            headers=user_session["jwt_headers"],
        )
        assert sessions.status_code == 200
        data = sessions.json()
        assert data["total"] == 1
        session = data["sessions"][0]
        assert session["session_id"] == "integration-001"
        assert session["duration_s"] == 180.0
        assert session["autorouter_matches"] == 1
        assert session["autorouter_misses"] == 1

    async def test_session_detail_and_events(
        self, client: AsyncClient, user_session: dict
    ):
        """Verify session detail includes event count and events are ordered."""
        base_time = datetime.now(UTC) - timedelta(hours=2)
        body = _build_session_events("integration-002", base_time)

        await client.post(
            "/api/v1/telemetry/ingest",
            json=body,
            headers=user_session["api_key_headers"],
        )

        # Session detail
        detail = await client.get(
            "/api/v1/telemetry/sessions/integration-002",
            headers=user_session["jwt_headers"],
        )
        assert detail.status_code == 200
        assert detail.json()["event_count"] == len(body["events"])

        # Session events
        events = await client.get(
            "/api/v1/telemetry/sessions/integration-002/events",
            headers=user_session["jwt_headers"],
        )
        assert events.status_code == 200
        event_data = events.json()
        assert event_data["total"] == len(body["events"])
        types = [e["event_type"] for e in event_data["events"]]
        assert types[0] == "session.start"
        assert types[-1] == "session.end"

    async def test_metrics_after_multi_session_ingest(
        self, client: AsyncClient, user_session: dict
    ):
        """Ingest multiple sessions, verify aggregate metrics are correct."""
        now = datetime.now(UTC)

        # Ingest 3 sessions with different plugins and times
        sessions_data = [
            _build_session_events(
                "metrics-001",
                now - timedelta(hours=3),
                duration_s=120.0,
                plugins=["core-kit"],
                skills={"core-kit:routing": 3},
            ),
            _build_session_events(
                "metrics-002",
                now - timedelta(hours=2),
                duration_s=240.0,
                plugins=["core-kit", "cloud-python-engineer"],
                skills={"cloud-python-engineer:engineer": 2},
            ),
            _build_session_events(
                "metrics-003",
                now - timedelta(hours=1),
                duration_s=60.0,
                plugins=["cloud-python-engineer"],
                skills={"cloud-python-engineer:engineer": 1},
            ),
        ]

        for body in sessions_data:
            resp = await client.post(
                "/api/v1/telemetry/ingest",
                json=body,
                headers=user_session["api_key_headers"],
            )
            assert resp.status_code == 202

        # Summary metrics
        summary = await client.get(
            "/api/v1/telemetry/metrics/summary",
            params={"period": "month"},
            headers=user_session["jwt_headers"],
        )
        assert summary.status_code == 200
        data = summary.json()
        assert data["total_sessions"] == 3
        assert data["period"] == "month"
        # autorouter_hit_rate: each session has 1 match + 1 miss = 0.5 per session
        assert data["autorouter_hit_rate"] == 0.5

    async def test_skill_heatmap_data(self, client: AsyncClient, user_session: dict):
        """Verify skill heatmap buckets contain correct skill counts."""
        base_time = datetime.now(UTC) - timedelta(hours=1)
        body = _build_session_events(
            "heatmap-001",
            base_time,
            skills={"core-kit:routing": 3, "cloud-python-engineer:engineer": 1},
        )

        await client.post(
            "/api/v1/telemetry/ingest",
            json=body,
            headers=user_session["api_key_headers"],
        )

        resp = await client.get(
            "/api/v1/telemetry/metrics/skills",
            params={"period": "day"},
            headers=user_session["jwt_headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["buckets"]) > 0
        # Verify skill names appear in buckets
        skills_in_buckets = {b["skill"] for b in data["buckets"]}
        assert "core-kit:routing" in skills_in_buckets

    async def test_plugin_metrics_data(self, client: AsyncClient, user_session: dict):
        """Verify plugin comparison metrics aggregate correctly."""
        base_time = datetime.now(UTC) - timedelta(hours=1)
        body = _build_session_events(
            "plugins-001",
            base_time,
            plugins=["core-kit", "cloud-python-engineer"],
        )

        await client.post(
            "/api/v1/telemetry/ingest",
            json=body,
            headers=user_session["api_key_headers"],
        )

        resp = await client.get(
            "/api/v1/telemetry/metrics/plugins",
            headers=user_session["jwt_headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        plugin_names = [p["plugin"] for p in data["plugins"]]
        assert "core-kit" in plugin_names
        assert "cloud-python-engineer" in plugin_names

    async def test_cost_and_token_endpoints(
        self, client: AsyncClient, user_session: dict
    ):
        """Verify cost and token endpoints return valid structure."""
        base_time = datetime.now(UTC) - timedelta(hours=1)
        body = _build_session_events("cost-001", base_time)

        await client.post(
            "/api/v1/telemetry/ingest",
            json=body,
            headers=user_session["api_key_headers"],
        )

        # Token usage
        tokens = await client.get(
            "/api/v1/telemetry/metrics/tokens",
            params={"period": "day"},
            headers=user_session["jwt_headers"],
        )
        assert tokens.status_code == 200

        # Cost over time
        cost = await client.get(
            "/api/v1/telemetry/metrics/cost",
            params={"period": "day"},
            headers=user_session["jwt_headers"],
        )
        assert cost.status_code == 200
        assert "total_cost_usd" in cost.json()

    async def test_plugin_filter_on_sessions(
        self, client: AsyncClient, user_session: dict
    ):
        """Verify the plugin query parameter filters sessions correctly."""
        base_time = datetime.now(UTC) - timedelta(hours=1)

        # Session with only core-kit
        body1 = _build_session_events(
            "filter-001",
            base_time,
            plugins=["core-kit"],
            skills={"core-kit:routing": 1},
        )
        await client.post(
            "/api/v1/telemetry/ingest",
            json=body1,
            headers=user_session["api_key_headers"],
        )

        # Session with cloud-python-engineer
        body2 = _build_session_events(
            "filter-002",
            base_time + timedelta(minutes=10),
            plugins=["cloud-python-engineer"],
            skills={"cloud-python-engineer:engineer": 1},
        )
        await client.post(
            "/api/v1/telemetry/ingest",
            json=body2,
            headers=user_session["api_key_headers"],
        )

        # Filter by cloud-python-engineer — should only return 1 session
        resp = await client.get(
            "/api/v1/telemetry/sessions",
            params={"plugin": "cloud-python-engineer"},
            headers=user_session["jwt_headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["sessions"][0]["session_id"] == "filter-002"

    async def test_date_range_filter(self, client: AsyncClient, user_session: dict):
        """Verify from_date/to_date filters restrict session results."""
        old_time = datetime.now(UTC) - timedelta(days=7)
        recent_time = datetime.now(UTC) - timedelta(hours=1)

        body1 = _build_session_events("date-001", old_time, plugins=["core-kit"])
        body2 = _build_session_events("date-002", recent_time, plugins=["core-kit"])

        for body in [body1, body2]:
            await client.post(
                "/api/v1/telemetry/ingest",
                json=body,
                headers=user_session["api_key_headers"],
            )

        # Query only recent sessions (last 2 hours)
        cutoff = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
        resp = await client.get(
            "/api/v1/telemetry/sessions",
            params={"from_date": cutoff},
            headers=user_session["jwt_headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["sessions"][0]["session_id"] == "date-002"


class TestAuthIsolation:
    """Verify that users can only see their own telemetry data."""

    async def test_cross_user_isolation(self, client: AsyncClient):
        """User A's data is not visible to User B."""
        # Register two users
        reg_a = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user-a@example.com",
                "password": "securepassword123",
                "display_name": "User A",
            },
        )
        jwt_a = {"Authorization": f"Bearer {reg_a.json()['access_token']}"}

        reg_b = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user-b@example.com",
                "password": "securepassword123",
                "display_name": "User B",
            },
        )
        jwt_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

        # User A ingests a session
        base_time = datetime.now(UTC) - timedelta(hours=1)
        body = _build_session_events("isolated-001", base_time)
        await client.post(
            "/api/v1/telemetry/ingest",
            json=body,
            headers=jwt_a,
        )

        # User A sees the session
        resp_a = await client.get(
            "/api/v1/telemetry/sessions",
            headers=jwt_a,
        )
        assert resp_a.json()["total"] == 1

        # User B sees nothing
        resp_b = await client.get(
            "/api/v1/telemetry/sessions",
            headers=jwt_b,
        )
        assert resp_b.json()["total"] == 0

        # User B cannot access User A's session detail
        resp_b_detail = await client.get(
            "/api/v1/telemetry/sessions/isolated-001",
            headers=jwt_b,
        )
        assert resp_b_detail.status_code == 404
