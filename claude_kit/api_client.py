"""Lightweight HTTP client for the claude-kit telemetry API.

Uses only stdlib (http.client, urllib.parse) — no third-party deps.
"""

from __future__ import annotations

import http.client
import json
import urllib.parse


class APIClient:
    """HTTP client for uploading telemetry events to the claude-kit API.

    Args:
        base_url: Base URL of the API (e.g. "http://localhost:8000").
        api_key: API key for authentication via X-API-Key header.
    """

    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def upload(self, session_id: str, events: list[dict]) -> bool:
        """Upload a batch of telemetry events.

        Args:
            session_id: Session UUID string.
            events: List of event dicts to upload.

        Returns:
            True if upload succeeded (2xx response), False otherwise.
        """
        if not events:
            return True  # nothing to upload is not a failure

        body = json.dumps({"session_id": session_id, "events": events})
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        }

        parsed = urllib.parse.urlparse(self.base_url)
        host = parsed.hostname or "localhost"
        port = parsed.port
        use_https = parsed.scheme == "https"
        path = f"{parsed.path}/api/v1/telemetry/ingest"

        for attempt in range(2):  # one retry on failure
            try:
                if use_https:
                    conn = http.client.HTTPSConnection(host, port, timeout=5)
                else:
                    conn = http.client.HTTPConnection(host, port, timeout=5)
                conn.request("POST", path, body=body, headers=headers)
                resp = conn.getresponse()
                conn.close()
                if 200 <= resp.status < 300:
                    return True
                if attempt == 0:
                    continue
                return False
            except (OSError, http.client.HTTPException):
                if attempt == 0:
                    continue
                return False
        return False

    def healthcheck(self) -> bool:
        """Check if the API is reachable.

        Returns:
            True if the API responds with 200 at /healthz.
        """
        parsed = urllib.parse.urlparse(self.base_url)
        host = parsed.hostname or "localhost"
        port = parsed.port
        use_https = parsed.scheme == "https"
        path = f"{parsed.path}/healthz"

        try:
            if use_https:
                conn = http.client.HTTPSConnection(host, port, timeout=5)
            else:
                conn = http.client.HTTPConnection(host, port, timeout=5)
            conn.request("GET", path)
            resp = conn.getresponse()
            conn.close()
            return resp.status == 200
        except (OSError, http.client.HTTPException):
            return False
