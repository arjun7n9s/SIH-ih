"""Layered fetch for IIITDMJ.

1. curl_cffi Chrome impersonation (free) — enough when the WAF only checks TLS.
2. Bright Data Web Unlocker — when the site 403s (homepage /academics does).
"""

from __future__ import annotations

from curl_cffi import requests as cffi_requests

from app.services.unlocker import UnlockerError, fetch_unlocker, unlocker_configured

BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
IMPERSONATE = "chrome124"


class FetchError(RuntimeError):
    pass


def fetch_bytes(url: str, *, want_pdf: bool = False) -> tuple[bytes, str]:
    """Return (body, via) where via is 'curl_cffi' or 'unlocker'."""
    err: Exception | None = None
    try:
        res = cffi_requests.get(
            url,
            impersonate=IMPERSONATE,
            headers={"User-Agent": BROWSER_UA, "Accept": "*/*"},
            timeout=45,
            allow_redirects=True,
        )
        if res.status_code == 200 and res.content:
            if want_pdf and not _looks_like_pdf(res.content):
                err = FetchError(f"curl_cffi 200 but not a PDF for {url}")
            else:
                return res.content, "curl_cffi"
        else:
            err = FetchError(f"curl_cffi HTTP {res.status_code} for {url}")
    except Exception as exc:  # noqa: BLE001 — fallback is the point
        err = exc

    if unlocker_configured():
        body = fetch_unlocker(url, markdown=not want_pdf)
        return body, "unlocker"

    if isinstance(err, UnlockerError):
        raise err
    raise FetchError(f"fetch failed for {url}: {err}")


def fetch_text(url: str) -> tuple[str, str]:
    body, via = fetch_bytes(url, want_pdf=False)
    return body.decode("utf-8", errors="replace"), via


def _looks_like_pdf(content: bytes) -> bool:
    return content[:5] == b"%PDF-" or b"%PDF-" in content[:1024]
