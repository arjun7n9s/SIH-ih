"""Bright Data Web Unlocker — the working Tingle path.

Tingle's Scraper Studio collectors (`POST /dca/trigger` + pinned c_*) are
site-specific CSS extractors that break when markup moves. Do not reuse them.

This is a Python port of Tingle `packages/tingle-core/src/bd/unlocker.ts`:
POST https://api.brightdata.com/request with zone + data_format=markdown.
"""

from __future__ import annotations

import httpx

from app.config import settings

UNLOCKER_URL = "https://api.brightdata.com/request"


class UnlockerError(RuntimeError):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def unlocker_configured() -> bool:
    return bool(settings.bd_token and settings.bright_data_unlocker_zone)


def fetch_unlocker(url: str, *, markdown: bool = True, timeout: float = 90.0) -> bytes:
    if not unlocker_configured():
        raise UnlockerError("missing BRIGHT_DATA_API_TOKEN or BRIGHT_DATA_UNLOCKER_ZONE")

    payload: dict = {
        "zone": settings.bright_data_unlocker_zone,
        "url": url,
        "format": "raw",
    }
    if markdown:
        payload["data_format"] = "markdown"

    headers = {
        "Authorization": f"Bearer {settings.bd_token}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=timeout) as client:
        res = client.post(UNLOCKER_URL, json=payload, headers=headers)
    if not res.is_success:
        raise UnlockerError(
            f"Web Unlocker failed HTTP {res.status_code} for {url}",
            res.status_code,
        )
    return res.content


def fetch_unlocker_markdown(url: str) -> str:
    return fetch_unlocker(url, markdown=True).decode("utf-8", errors="replace")
