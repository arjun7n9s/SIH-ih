"""Build data/index/faculty.json from faculty.iiitdmj.ac.in + department pages.

Uses curl_cffi only (short timeout). Does not call Bright Data — profile 500s used
to stall for 90s each on the unlocker fallback.
"""

from __future__ import annotations

import json
import re
import sys
import time
from html import unescape
from pathlib import Path
from urllib.parse import urljoin

from curl_cffi import requests as cffi_requests
from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))
load_dotenv(REPO / ".env")

OUT = REPO / "data" / "index" / "faculty.json"
HOME = "http://faculty.iiitdmj.ac.in/"
DEPT_PAGES = [
    "https://ece.iiitdmj.ac.in/faculty.html",
    "https://www.iiitdmj.ac.in/cse.iiitdmj.ac.in/www.web.iiitdmj.ac.in/faculty.php",
    "https://me.iiitdmj.ac.in/faculty.html",
]
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@iiitdmj\.ac\.in", re.I)
PHONE_RE = re.compile(r"(?:\+91[- ]?)?(?:0?761[- ]?)?\d{6,10}")
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

CARD_RE = re.compile(
    r"<h4>([^<]{3,90})</h4>\s*"
    r"<p[^>]*>([^<]{0,160})</p>\s*"
    r"<h4[^>]*>\s*<small>([^<]*)</small>\s*</h4>\s*"
    r"(?:<p[^>]*>([^<]{0,240})</p>\s*)?"
    r"""[\s\S]{0,220}?href=["']([^"']*?/faculty/([a-zA-Z0-9._-]+))["']""",
    re.I,
)


def _get(url: str, timeout: float = 15.0) -> tuple[int, str]:
    res = cffi_requests.get(
        url,
        impersonate="chrome124",
        headers={"User-Agent": BROWSER_UA, "Accept": "*/*"},
        timeout=timeout,
        allow_redirects=True,
    )
    body = (res.text or "") if res.content else ""
    return res.status_code, body


def _clean(s: str) -> str:
    s = unescape(s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip(" -:;|")


def _parse_home(html: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for name, dept, designation, research, href, slug in CARD_RE.findall(html):
        slug = slug.lower()
        url = urljoin(HOME, href)
        row = {
            "name": _clean(name),
            "email": None,
            "phone": None,
            "department": _clean(dept) or None,
            "designation": _clean(designation) or None,
            "research": _clean(research) or None,
            "profile_url": url,
            "slug": slug,
        }
        prev = out.get(slug)
        if prev and prev.get("research") and not row["research"]:
            row["research"] = prev["research"]
        out[slug] = row
    return out


def _emails_from_html(html: str) -> dict[str, str]:
    """local-part → email, skip generic mailboxes."""
    skip = {"question", "info", "admin", "webmaster", "office", "dean.s"}
    found: dict[str, str] = {}
    for email in EMAIL_RE.findall(html):
        email = email.lower()
        local = email.split("@")[0]
        if local in skip or local.isdigit():
            continue
        found[local] = email
    return found


def _phones_from_dept(html: str) -> dict[str, str]:
    """Best-effort: phone sitting near an institute email on dept pages."""
    out: dict[str, str] = {}
    plain = re.sub(r"<[^>]+>", " ", html)
    for m in EMAIL_RE.finditer(html):
        email = m.group(0).lower()
        window = html[max(0, m.start() - 500) : m.end() + 200]
        window = re.sub(r"<[^>]+>", " ", window)
        phones = PHONE_RE.findall(window)
        if phones:
            out[email] = phones[0]
    return out


def _parse_profile(html: str, slug: str, url: str, existing: dict) -> dict:
    emails = [e.lower() for e in EMAIL_RE.findall(html)]
    email = next((e for e in emails if e.endswith("@iiitdmj.ac.in")), emails[0] if emails else None)
    phones = PHONE_RE.findall(re.sub(r"<[^>]+>", " ", html))
    row = dict(existing)
    if email:
        row["email"] = email
    if phones and not row.get("phone"):
        row["phone"] = phones[0]
    if not row.get("name"):
        row["name"] = slug.replace(".", " ").replace("_", " ").title()
    row["profile_url"] = url
    row["slug"] = slug
    return row


def main() -> int:
    print("Fetching faculty home…", flush=True)
    status, home = _get(HOME, timeout=25)
    print(f"  home HTTP {status}, {len(home)} bytes", flush=True)
    if status != 200 or not home:
        print("faculty home failed", flush=True)
        return 1

    html_dir = REPO / "data" / "corpus" / "html"
    html_dir.mkdir(parents=True, exist_ok=True)
    (html_dir / "faculty-home.md").write_text(
        f"<!-- source: {HOME} -->\n\n{home[:200000]}", encoding="utf-8"
    )

    by_slug = _parse_home(home)
    print(f"  cards: {len(by_slug)}", flush=True)

    email_map: dict[str, str] = {}
    phone_map: dict[str, str] = {}
    for url in DEPT_PAGES:
        try:
            st, html = _get(url)
            print(f"  dept {st} {len(html)} {url}", flush=True)
            email_map.update(_emails_from_html(html))
            phone_map.update(_phones_from_dept(html))
        except Exception as err:  # noqa: BLE001
            print(f"  dept fail {url}: {err}", flush=True)

    matched = 0
    for slug, row in by_slug.items():
        if slug in email_map:
            row["email"] = email_map[slug]
            matched += 1
        elif row.get("email"):
            matched += 1
        email = row.get("email")
        if email and email in phone_map:
            row["phone"] = phone_map[email]
    print(f"  emails matched by slug: {matched}/{len(by_slug)}", flush=True)

    # Fill remaining from profile pages (skip HTTP errors; no unlocker).
    missing = [s for s, r in by_slug.items() if not r.get("email")]
    print(f"  profile fetch for {len(missing)} without email", flush=True)
    for i, slug in enumerate(missing, start=1):
        url = by_slug[slug].get("profile_url") or urljoin(HOME, f"/faculty/{slug}")
        try:
            st, html = _get(url, timeout=12)
            if st == 200 and html:
                by_slug[slug] = _parse_profile(html, slug, url, by_slug[slug])
            if i % 10 == 0:
                print(f"    profiles {i}/{len(missing)}", flush=True)
            time.sleep(0.03)
        except Exception as err:  # noqa: BLE001
            print(f"    skip {slug}: {err}", flush=True)

    # Last resort: slug@iiitdmj.ac.in when that mailbox appeared on a dept page
    # (already applied) — do not invent other mailboxes.

    # Also keep dept-only people not on the home grid
    known_emails = {r.get("email") for r in by_slug.values() if r.get("email")}
    extra = 0
    for local, email in email_map.items():
        if email in known_emails:
            continue
        by_slug[local] = {
            "name": local.replace(".", " ").replace("_", " ").title(),
            "email": email,
            "phone": phone_map.get(email),
            "department": None,
            "designation": None,
            "research": None,
            "profile_url": urljoin(HOME, f"/faculty/{local}"),
            "slug": local,
        }
        extra += 1
    print(f"  extra dept-only: {extra}", flush=True)

    rows = sorted(by_slug.values(), key=lambda r: (r.get("name") or "").lower())
    with_email = sum(1 for r in rows if r.get("email"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"items": rows, "source": HOME, "count": len(rows)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {len(rows)} faculty ({with_email} with email) -> {OUT}", flush=True)
    return 0 if with_email else 1


if __name__ == "__main__":
    raise SystemExit(main())
