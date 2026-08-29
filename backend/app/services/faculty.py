"""Faculty answers from faculty.iiitdmj.ac.in — scraped, not hand-typed."""

from __future__ import annotations

import json
import re
import time
from functools import lru_cache
from html import unescape
from pathlib import Path
from urllib.parse import urljoin

from app.services.store import REPO

HOME = "http://faculty.iiitdmj.ac.in/"
_PACKAGED = Path(__file__).resolve().parents[1] / "faculty_data.json"
_INDEXED = REPO / "data" / "index" / "faculty.json"
_TTL_SEC = 6 * 3600

_CARD_RE = re.compile(
    r"<h4>([^<]{3,90})</h4>\s*"
    r"<p[^>]*>([^<]{0,160})</p>\s*"
    r"<h4[^>]*>\s*<small>([^<]*)</small>\s*</h4>\s*"
    r"(?:<p[^>]*>([^<]{0,240})</p>\s*)?"
    r"""[\s\S]{0,220}?href=["']([^"']*?/faculty/([a-zA-Z0-9._-]+))["']""",
    re.I,
)
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@iiitdmj\.ac\.in", re.I)
_PHONE_RE = re.compile(r"(?:\+91[- ]?)?(?:0?761[- ]?)?\d{6,10}")

_STOP = {
    "what", "who", "whom", "email", "mail", "e-mail", "faculty", "professor",
    "prof", "the", "of", "is", "for", "please", "tell", "me", "contact",
    "phone", "number", "id", "address", "give", "need", "want", "from",
    "ka", "ki", "ke", "kya", "hai", "hain",
    "का", "की", "के", "क्या", "है", "हैं", "बताओ", "बताइए", "दीजिए",
    "ईमेल", "मेल", "प्रोफेसर", "फैकल्टी", "फैकलटी", "सर", "मैम",
    "area", "research", "interest", "expertise", "field",
}

_last_refresh = 0.0


def _norm(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9\u0900-\u097F\s@.]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _compact(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _strip_titles(s: str) -> str:
    return re.sub(
        r"\b(dr|prof|professor|mr|ms|mrs|sir|madam|डॉ|प्रो)\b\.?",
        " ",
        s,
        flags=re.I,
    )


def _clean(s: str) -> str:
    s = unescape(s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip(" -:;|")


def _wants_research(query: str) -> bool:
    return bool(
        re.search(
            r"research|expertise|speciali[sz]|works on|area of|interest|"
            r"शोध|रिसर्च",
            query or "",
            re.I,
        )
    )


def _load_disk() -> list[dict]:
    for path in (_INDEXED, _PACKAGED):
        if path.exists():
            try:
                items = json.loads(path.read_text(encoding="utf-8")).get("items") or []
                if items:
                    return items
            except Exception:  # noqa: BLE001
                continue
    return []


def _save_disk(rows: list[dict]) -> None:
    payload = json.dumps(
        {"items": rows, "source": HOME, "count": len(rows)},
        ensure_ascii=False,
        indent=2,
    )
    for path in (_INDEXED, _PACKAGED):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(payload, encoding="utf-8")
        except OSError:
            continue


@lru_cache(maxsize=1)
def all_faculty() -> list[dict]:
    return _load_disk()


def clear_cache() -> None:
    all_faculty.cache_clear()


def _parse_home(html: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for name, dept, designation, research, href, slug in _CARD_RE.findall(html):
        slug = slug.lower()
        row = {
            "name": _clean(name),
            "email": None,
            "phone": None,
            "department": _clean(dept) or None,
            "designation": _clean(designation) or None,
            "research": _clean(research) or None,
            "profile_url": urljoin(HOME, href),
            "slug": slug,
        }
        prev = out.get(slug)
        if prev and prev.get("research") and not row["research"]:
            row["research"] = prev["research"]
        if prev and prev.get("email"):
            row["email"] = prev["email"]
        out[slug] = row
    return out


def _fetch_text(url: str, timeout: float = 18.0) -> str:
    from curl_cffi import requests as cffi_requests

    res = cffi_requests.get(
        url,
        impersonate="chrome124",
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
        },
        timeout=timeout,
        allow_redirects=True,
    )
    if res.status_code != 200 or not res.content:
        return ""
    return res.text or ""


def refresh_directory(*, force: bool = False) -> list[dict]:
    """Pull the live faculty grid (name, dept, research). Keep known emails."""
    global _last_refresh
    cached = all_faculty()
    if cached and not force and (time.time() - _last_refresh) < _TTL_SEC:
        return cached
    if cached and not force and _last_refresh == 0:
        # First call this process: use disk immediately, refresh in the same request
        # only when we actually need missing research (see lookup).
        _last_refresh = time.time()
        return cached
    try:
        html = _fetch_text(HOME, timeout=20)
    except Exception:  # noqa: BLE001
        return cached
    if not html:
        return cached
    cards = _parse_home(html)
    if not cards:
        return cached
    by_slug = {((r.get("slug") or "").lower()): dict(r) for r in cached}
    for slug, card in cards.items():
        cur = by_slug.get(slug) or {}
        merged = {**cur, **{k: v for k, v in card.items() if v}}
        if cur.get("email") and not merged.get("email"):
            merged["email"] = cur["email"]
        if cur.get("phone") and not merged.get("phone"):
            merged["phone"] = cur["phone"]
        by_slug[slug] = merged
    rows = sorted(by_slug.values(), key=lambda r: (r.get("name") or "").lower())
    _save_disk(rows)
    clear_cache()
    _last_refresh = time.time()
    return rows


def _fill_from_profile(row: dict) -> dict:
    url = row.get("profile_url") or ""
    if not url:
        return row
    try:
        html = _fetch_text(url, timeout=12)
    except Exception:  # noqa: BLE001
        return row
    if not html:
        return row
    emails = [e.lower() for e in _EMAIL_RE.findall(html)]
    inst = next((e for e in emails if e.endswith("@iiitdmj.ac.in")), emails[0] if emails else None)
    if inst and not row.get("email"):
        row["email"] = inst
    phones = _PHONE_RE.findall(re.sub(r"<[^>]+>", " ", html))
    if phones and not row.get("phone"):
        row["phone"] = phones[0]
    if not row.get("research"):
        m = re.search(
            r"(?:Research(?:\s+Interest)?s?|Areas? of Interest)\s*[:\-]?\s*([^<]{8,240})",
            html,
            re.I,
        )
        if m:
            row["research"] = _clean(m.group(1))
    return row


def directory_prompt() -> str:
    rows = all_faculty()
    if not rows:
        return ""
    lines = ["name | email | department | designation | research"]
    for r in rows:
        lines.append(
            " | ".join(
                [
                    r.get("name") or r.get("slug") or "",
                    r.get("email") or "",
                    r.get("department") or "",
                    r.get("designation") or "",
                    r.get("research") or "",
                ]
            )
        )
    return "\n".join(lines)


def _score(query: str, row: dict) -> float:
    q = _norm(_strip_titles(query))
    qc = _compact(q)
    name = _norm(row.get("name") or "")
    nc = _compact(name)
    slug = _norm(row.get("slug") or "")
    sc = _compact(slug)
    email = _norm(row.get("email") or "")
    local = email.split("@")[0] if email else ""
    lc = _compact(local)
    if not q:
        return 0.0
    score = 0.0
    if name and name in q:
        score += 8.0
    if nc and len(nc) > 5 and nc in qc:
        score += 8.0
    if sc and len(sc) > 4 and sc in qc:
        score += 7.0
    if lc and len(lc) > 4 and lc in qc:
        score += 7.0
    q_tokens = [t for t in q.split() if len(t) > 2 and t not in _STOP]
    name_tokens = set(name.split())
    blob = f"{name} {slug} {local} {nc} {sc} {lc}"
    hits = 0
    for t in q_tokens:
        tc = _compact(t)
        if t in name_tokens or tc in blob or (len(tc) > 3 and tc in nc):
            hits += 1
            score += 2.0
    if hits >= 2:
        score += 3.0
    return score


def search(query: str, limit: int = 5) -> list[tuple[float, dict]]:
    ranked = sorted(((_score(query, r), r) for r in all_faculty()), key=lambda x: x[0], reverse=True)
    return [(s, r) for s, r in ranked if s >= 2.0][:limit]


def looks_like_faculty_query(query: str) -> bool:
    q = query.lower()
    if re.search(
        r"\bdirector\b|\bregistrar\b|vice.?chancellor|निदेशक|डायरेक्टर|रजिस्ट्रार",
        q,
    ):
        return False
    if re.search(r"faculty\.iiitdmj|@iiitdmj\.ac\.in", q):
        return True
    contactish = bool(
        re.search(
            r"email|e-mail|mail id|mailid|phone|mobile|"
            r"research|expertise|speciali[sz]e|works on|area of|"
            r"ईमेल|इमेल|मेल\s*आईडी|फोन|मोबाइल|शोध|रिसर्च",
            q,
        )
    )
    personish = bool(
        re.search(
            r"faculty|professor|\bprof\b|\bdr\b|डॉ\.?|प्रो\.?|sir|madam|"
            r"फैकल्टी|फैकलटी|प्रोफेसर",
            q,
        )
    )
    if contactish or personish:
        return True
    hits = search(query, limit=1)
    return bool(hits and hits[0][0] >= 6.0)


def lookup(query: str) -> list[dict]:
    if not all_faculty() or (
        _wants_research(query) and not any(r.get("research") for r in all_faculty())
    ):
        refresh_directory(force=True)
    hits = search(query)
    if _wants_research(query) and hits and not hits[0][1].get("research"):
        refresh_directory(force=True)
        hits = search(query)
        if hits and not hits[0][1].get("research"):
            filled = _fill_from_profile(dict(hits[0][1]))
            hits[0] = (hits[0][0], filled)
            # persist that one row
            rows = all_faculty()
            for i, r in enumerate(rows):
                if (r.get("slug") or "") == (filled.get("slug") or ""):
                    rows[i] = filled
                    _save_disk(rows)
                    clear_cache()
                    break
    if not hits:
        return []
    # Research / email of one person: don't dump every similar last name
    if _wants_research(query) or re.search(r"email|phone|ईमेल|फोन", query, re.I):
        if len(hits) == 1 or hits[0][0] >= hits[1][0] + 2.5:
            return [hits[0][1]]
    return [r for _, r in hits]


def source_cards(rows: list[dict]) -> list[dict]:
    url = (rows[0].get("profile_url") if rows else None) or HOME
    return [
        {
            "n": 1,
            "title": "Faculty directory",
            "url": url,
            "page": None,
            "excerpt": "faculty.iiitdmj.ac.in",
            "effective_from": None,
            "last_updated": None,
            "document_id": "faculty-directory",
        }
    ]


def format_answer(rows: list[dict], query: str) -> str:
    hindi = bool(re.search(r"[\u0900-\u097F]", query))
    if not rows:
        if hindi:
            return "डायरेक्टरी में यह नाम नहीं मिला — http://faculty.iiitdmj.ac.in/ पर देखें।"
        return "No exact directory match — check http://faculty.iiitdmj.ac.in/"
    lines: list[str] = []
    for r in rows[:3]:
        bits = [f"**{r.get('name') or r.get('slug')}**"]
        if r.get("designation"):
            bits.append(r["designation"])
        if r.get("department"):
            bits.append(r["department"])
        detail = []
        if r.get("research"):
            detail.append(f"Research: {r['research']}")
        if r.get("email"):
            detail.append(f"Email: `{r['email']}`")
        if r.get("phone"):
            detail.append(f"Phone: {r['phone']}")
        if r.get("profile_url"):
            detail.append(f"Profile: {r['profile_url']}")
        lines.append(" — ".join(bits) + ("\n" + "\n".join(detail) if detail else ""))
    if hindi:
        return "फैकल्टी डायरेक्टरी:\n\n" + "\n\n".join(lines)
    return "From the faculty directory:\n\n" + "\n\n".join(lines)
