"""Client for NeXroll's stable integration API (see docs/nexroll-integration.md).

Auth is via ``X-Api-Key``. Bingearr owns both projects, so this talks to a
small public surface on NeXroll rather than its internal endpoints.
"""

from __future__ import annotations

import httpx


class NeXrollClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 15) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    @property
    def _headers(self) -> dict:
        return {"X-Api-Key": self.api_key}

    def _url(self, path: str) -> str:
        return f"{self.base_url}/api/integration/{path}"

    def status(self) -> dict:
        r = httpx.get(self._url("status"), headers=self._headers, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def list_prerolls(self) -> list[dict]:
        r = httpx.get(self._url("prerolls"), headers=self._headers, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def apply(self, ref: str, server: str | None = None) -> dict:
        r = httpx.post(
            self._url("apply"),
            json={"ref": ref, "server": server},
            headers=self._headers,
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def clear(self) -> dict:
        r = httpx.post(self._url("clear"), json={}, headers=self._headers, timeout=self.timeout)
        r.raise_for_status()
        return r.json()
