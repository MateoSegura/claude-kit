"""Tests for claude_kit.api_client — APIClient contracts.

TDD: These tests define the expected behavior of the APIClient
before implementation. Uses stdlib-only mocking (unittest.mock).
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch


def test_api_client_importable():
    from claude_kit.api_client import APIClient  # noqa: F401


def test_api_client_stores_config():
    from claude_kit.api_client import APIClient

    client = APIClient(base_url="http://localhost:8000", api_key="test-key")
    assert client.base_url == "http://localhost:8000"
    assert client.api_key == "test-key"


def test_api_client_strips_trailing_slash():
    from claude_kit.api_client import APIClient

    client = APIClient(base_url="http://localhost:8000/", api_key="k")
    assert client.base_url == "http://localhost:8000"


def test_upload_returns_true_on_success():
    from claude_kit.api_client import APIClient

    client = APIClient(base_url="http://localhost:8000", api_key="key")
    mock_resp = MagicMock()
    mock_resp.status = 202
    mock_conn = MagicMock()
    mock_conn.getresponse.return_value = mock_resp

    with patch("http.client.HTTPConnection", return_value=mock_conn):
        result = client.upload(
            session_id="abc-123",
            events=[{"event_type": "test", "timestamp": "now", "payload": {}}],
        )
    assert result is True


def test_upload_returns_false_on_server_error():
    from claude_kit.api_client import APIClient

    client = APIClient(base_url="http://localhost:8000", api_key="key")
    mock_resp = MagicMock()
    mock_resp.status = 500
    mock_conn = MagicMock()
    mock_conn.getresponse.return_value = mock_resp

    with patch("http.client.HTTPConnection", return_value=mock_conn):
        result = client.upload(session_id="abc", events=[{"event_type": "t"}])
    assert result is False


def test_upload_returns_false_on_connection_error():
    from claude_kit.api_client import APIClient

    client = APIClient(base_url="http://localhost:8000", api_key="key")

    with patch("http.client.HTTPConnection", side_effect=OSError("connection refused")):
        result = client.upload(session_id="abc", events=[{"event_type": "t"}])
    assert result is False


def test_upload_sends_correct_headers():
    from claude_kit.api_client import APIClient

    client = APIClient(base_url="http://localhost:8000", api_key="my-api-key")
    mock_resp = MagicMock()
    mock_resp.status = 202
    mock_conn = MagicMock()
    mock_conn.getresponse.return_value = mock_resp

    with patch("http.client.HTTPConnection", return_value=mock_conn):
        client.upload(session_id="abc", events=[{"event_type": "t"}])

    call_args = mock_conn.request.call_args
    headers = call_args.kwargs.get("headers") or call_args.args[3]
    assert headers["Content-Type"] == "application/json"
    assert headers["X-API-Key"] == "my-api-key"


def test_upload_sends_correct_body():
    from claude_kit.api_client import APIClient

    client = APIClient(base_url="http://localhost:8000", api_key="key")
    mock_resp = MagicMock()
    mock_resp.status = 202
    mock_conn = MagicMock()
    mock_conn.getresponse.return_value = mock_resp

    events = [
        {
            "event_type": "session.start",
            "timestamp": "2026-03-01T00:00:00Z",
            "payload": {},
        },
    ]
    with patch("http.client.HTTPConnection", return_value=mock_conn):
        client.upload(session_id="abc-123", events=events)

    call_args = mock_conn.request.call_args
    body = call_args[1].get("body") or call_args[0][2]
    parsed = json.loads(body)
    assert parsed["session_id"] == "abc-123"
    assert len(parsed["events"]) == 1


def test_upload_empty_events_returns_true():
    from claude_kit.api_client import APIClient

    client = APIClient(base_url="http://localhost:8000", api_key="key")
    result = client.upload(session_id="abc", events=[])
    assert result is True


def test_upload_uses_https_for_https_url():
    from claude_kit.api_client import APIClient

    client = APIClient(base_url="https://api.example.com", api_key="key")
    mock_resp = MagicMock()
    mock_resp.status = 202
    mock_conn = MagicMock()
    mock_conn.getresponse.return_value = mock_resp

    with patch("http.client.HTTPSConnection", return_value=mock_conn) as mock_https:
        client.upload(session_id="abc", events=[{"event_type": "t"}])
    mock_https.assert_called_once()


def test_healthcheck_returns_true_on_200():
    from claude_kit.api_client import APIClient

    client = APIClient(base_url="http://localhost:8000", api_key="key")
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_conn = MagicMock()
    mock_conn.getresponse.return_value = mock_resp

    with patch("http.client.HTTPConnection", return_value=mock_conn):
        assert client.healthcheck() is True


def test_healthcheck_returns_false_on_error():
    from claude_kit.api_client import APIClient

    client = APIClient(base_url="http://localhost:8000", api_key="key")

    with patch("http.client.HTTPConnection", side_effect=OSError("down")):
        assert client.healthcheck() is False
