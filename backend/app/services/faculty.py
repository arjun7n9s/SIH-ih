"""Lookup faculty contacts from the seeded faculty.iiitdmj.ac.in index."""

from __future__ import annotations

import json
import re
from functools import lru_cache

from app.services.store import REPO

FACULTY_PATH = REPO / "data" / "index" / "faculty.json"
HOME = "http://faculty.iiitdmj.ac.in/"

# Hindi / spelling variants seen in student questions → index tokens
_ALIASES = {
    "प्रीती": "pritee pkhanna khanna",
    "प्रिति": "pritee pkhanna khanna",
    "प्रीति": "pritee pkhanna khanna",
    "खन्ना": "khanna pkhanna pritee",
    "अतुल": "atul gupta",
    "गुप्ता": "gupta atul",
    "ओझा": "ojha aojha aparajita",
    "अपरजिता": "aparajita ojha aojha",
    "पी.के.": "pkhanna",
    "sraban": "sraban",
    "शुभ्रांशु": "himansu",
}

_STOP = {
    "what", "who", "whom", "email", "mail", "e-mail", "faculty", "professor",
    "prof", "dr", "the", "of", "is", "for", "please", "tell", "me", "please",
    "contact", "phone", "number", "id", "address", "give", "need", "want",
    "ka", "ki", "ke", "kya", "hai", "hain",
    "का", "की", "के", "क्या", "है", "हैं", "बताओ", "बताइए", "दीजिए",
    "ईमेल", "मेल", "प्रोफेसर", "फैकल्टी", "फैकलटी", "सर", "मैम",
}


def _norm(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9\u0900-\u097F\s@.]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _expand(query: str) -> str:
    extra = []
    for token, mapped in _ALIASES.items():
        if token in query.lower() or token in query:
            extra.append(mapped)
    return query + (" " + " ".join(extra) if extra else "")


@lru_cache(maxsize=1)
def all_faculty() -> list[dict]:
    if not FACULTY_PATH.exists():
        return []
    data = json.loads(FACULTY_PATH.read_text(encoding="utf-8"))
    return data.get("items") or []


def clear_cache() -> None:
    all_faculty.cache_clear()


def _score(query: str, row: dict) -> float:
    q = _norm(_expand(query))
    name = _norm(row.get("name") or "")
    slug = _norm(row.get("slug") or "")
    email = _norm(row.get("email") or "")
    local = email.split("@")[0] if email else ""
    if not q:
        return 0.0
    score = 0.0
    if name and name in q:
        score += 6.0
    compact = q.replace(" ", "")
    if slug and slug in compact:
        score += 5.0
    if local and local in compact:
        score += 5.0
    q_tokens = [t for t in q.split() if len(t) > 2 and t not in _STOP]
    name_tokens = set(name.split())
    slug_tokens = set(slug.replace(".", " ").split())
    hits = 0
    for t in q_tokens:
        if t in name_tokens or t in slug_tokens or t == local or t in local:
            hits += 1
            score += 1.8
    if hits >= 2:
        score += 2.0
    # last-token last-name
    if q_tokens and (q_tokens[-1] in name_tokens or q_tokens[-1] == slug or q_tokens[-1] == local):
        score += 1.4
    return score


def search(query: str, limit: int = 5) -> list[tuple[float, dict]]:
    ranked = sorted(((_score(query, r), r) for r in all_faculty()), key=lambda x: x[0], reverse=True)
    return [(s, r) for s, r in ranked if s >= 1.6][:limit]


def looks_like_faculty_query(query: str) -> bool:
    q = query.lower()
    if re.search(
        r"email|e-mail|mail id|mailid|contact|phone|mobile|"
        r"ईमेल|इमेल|मेल\s*आईडी|संपर्क|फोन|मोबाइल|"
        r"प्रोफेसर|फैकल्टी|फैकलटी|faculty|professor|\bprof\b",
        q,
    ):
        return True
    if re.search(r"faculty\.iiitdmj|@iiitdmj\.ac\.in", q):
        return True
    # A directory hit on a person name is enough ("who is Atul Gupta")
    hits = search(query, limit=1)
    return bool(hits and hits[0][0] >= 4.5)


def english_name_hint(query: str) -> str | None:
    """If the question is Hindi, ask the chat model for the English faculty name."""
    if not re.search(r"[\u0900-\u097F]", query):
        return None
    from app.services import aimlapi
    from app.config import settings

    if not aimlapi.client():
        return None
    try:
        hint = aimlapi.chat_completion(
            "The user asked in Hindi about an IIITDM Jabalpur faculty member. "
            "Reply with only their name in English letters (example: Pritee Khanna). "
            "If there is no person, reply NONE.",
            query,
            temperature=0,
            max_tokens=24,
            model=settings.aimlapi_chat_model,
        )
    except Exception:  # noqa: BLE001
        return None
    hint = (hint or "").strip().strip('"')
    if not hint or hint.upper() == "NONE" or len(hint) > 60:
        return None
    return hint


def lookup(query: str) -> list[dict]:
    hits = search(query)
    if hits and hits[0][0] >= 2.4:
        return [r for _, r in hits]
    hint = english_name_hint(query)
    if hint:
        more = search(hint)
        if more:
            return [r for _, r in more]
    return [r for _, r in hits]


def source_cards(rows: list[dict]) -> list[dict]:
    sources: list[dict] = []
    for i, r in enumerate(rows[:3], start=1):
        sources.append(
            {
                "n": i,
                "title": r.get("name") or "Faculty directory",
                "url": r.get("profile_url") or HOME,
                "page": None,
                "excerpt": r.get("email") or r.get("department") or "",
                "effective_from": None,
                "last_updated": None,
                "document_id": "faculty-directory",
            }
        )
    if not sources:
        sources.append(
            {
                "n": 1,
                "title": "Faculty directory — IIITDM Jabalpur",
                "url": HOME,
                "page": None,
                "excerpt": "faculty.iiitdmj.ac.in",
                "effective_from": None,
                "last_updated": None,
                "document_id": "faculty-directory",
            }
        )
    return sources


def format_answer(rows: list[dict], query: str) -> str:
    hindi = bool(re.search(r"[\u0900-\u097F]", query))
    if not rows:
        if hindi:
            return (
                "इंडेक्स में यह नाम नहीं मिला। पूरा अंग्रेज़ी नाम लिखकर देखें, "
                "या http://faculty.iiitdmj.ac.in/ खोलें।"
            )
        return (
            "I couldn’t match that name in the faculty directory. "
            "Try the exact spelling, or open http://faculty.iiitdmj.ac.in/"
        )
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
        return "फैकल्टी डायरेक्टरी (faculty.iiitdmj.ac.in):\n\n" + "\n\n".join(lines)
    return "From the faculty directory (faculty.iiitdmj.ac.in):\n\n" + "\n\n".join(lines)
