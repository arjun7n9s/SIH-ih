"""Speechmatics temporary Realtime JWT mint."""

from __future__ import annotations

import httpx

from app.config import settings

URL = "https://mp.speechmatics.com/v1/api_keys"


def mint_rt_jwt(ttl: int | None = None) -> dict:
    if not settings.speechmatics_api_key:
        raise RuntimeError("SPEECHMATICS_API_KEY missing")
    ttl = ttl or settings.speechmatics_jwt_ttl_seconds
    ttl = max(60, min(int(ttl), 3600))
    res = httpx.post(
        URL,
        params={"type": "rt"},
        headers={
            "Authorization": f"Bearer {settings.speechmatics_api_key}",
            "Content-Type": "application/json",
        },
        json={"ttl": ttl},
        timeout=30,
    )
    if not res.is_success:
        raise RuntimeError(f"Speechmatics JWT failed HTTP {res.status_code}: {res.text[:200]}")
    body = res.json()
    token = body.get("key_value") or body.get("key") or body.get("token") or ""
    if not token:
        raise RuntimeError(f"Speechmatics JWT response missing key: {body}")
    return {
        "token": token,
        "ttl": ttl,
        "region_hint": "wss://global.rt.speechmatics.com/v2",
    }
