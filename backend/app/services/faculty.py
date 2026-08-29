"""Lookup faculty contacts from the seeded faculty.iiitdmj.ac.in index."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from app.services.store import REPO

HOME = "http://faculty.iiitdmj.ac.in/"
_PACKAGED = Path(__file__).resolve().parents[1] / "faculty_data.json"
_INDEXED = REPO / "data" / "index" / "faculty.json"

_STOP = {
    "what", "who", "whom", "email", "mail", "e-mail", "faculty", "professor",
    "prof", "the", "of", "is", "for", "please", "tell", "me", "contact",
    "phone", "number", "id", "address", "give", "need", "want", "from",
    "ka", "ki", "ke", "kya", "hai", "hain",
    "का", "की", "के", "क्या", "है", "हैं", "बताओ", "बताइए", "दीजिए",
    "ईमेल", "मेल", "प्रोफेसर", "फैकल्टी", "फैकलटी", "सर", "मैम",
}


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


@lru_cache(maxsize=1)
def all_faculty() -> list[dict]:
    for path in (_INDEXED, _PACKAGED):
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            items = data.get("items") or []
            if items:
                return items
    return []


def clear_cache() -> None:
    all_faculty.cache_clear()


def directory_prompt() -> str:
    rows = all_faculty()
    if not rows:
        return ""
    lines = ["name | email | department | designation"]
    for r in rows:
        lines.append(
            " | ".join(
                [
                    r.get("name") or r.get("slug") or "",
                    r.get("email") or "",
                    r.get("department") or "",
                    r.get("designation") or "",
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
            r"ईमेल|इमेल|मेल\s*आईडी|फोन|मोबाइल",
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
    return [r for _, r in search(query)]


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
