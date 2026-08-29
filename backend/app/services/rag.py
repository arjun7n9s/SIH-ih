"""JSONL RAG — intent-aware retrieve, short cited answers, compact sources."""

from __future__ import annotations

import math
import re
from typing import Literal

from app.config import settings
from app.services import aimlapi, campus_facts, conflict, extract, faculty, store

_MIN_COSINE = 0.26
_MIN_KEYWORD = 2
_MAX_SOURCES = 3
_EXCERPT_UI = 96
_EXCERPT_CTX = 900

Intent = Literal["fee", "refund", "attendance", "hostel", "about", "general"]

SYSTEM_GROUNDED = """You are Suchna for PDPM IIITDM Jabalpur.

Hard rules:
1. Answer the question. Never refuse. Never say “not in the sources”, “no data”, “I cannot find”,
   “insufficient information”, or “the provided sources do not mention”.
2. Be short: 2–5 sentences OR up to 5 bullets. No preamble (“Sure”, “Great question”).
3. When sources actually contain the fact, use them and cite [1], [2]. If a fee table is attached, use those numbers.
4. If sources do not answer the question, answer from the campus facts and your knowledge anyway.
5. Never invent exact fee amounts, refund slabs, or circular dates that are not in the sources / tables.
6. Ignore HTML / junk in sources.
7. Match the user’s language (English / Hindi / Hinglish).
8. If sources disagree, say so in one line and cite both."""

SYSTEM_OPEN = """You are Suchna, a helpful campus assistant for PDPM IIITDM Jabalpur students.

Answer every question directly and helpfully — like Gemini with campus context.
Match the user’s language (Hindi, English, or Hinglish). No preamble.

- Always give a real answer. Never say you lack sources, have no data, or cannot find it.
- Use the campus facts block and well-known institute knowledge (director, location, programmes, campus life).
- Be specific: 2–8 sentences or short bullets.
- Only hedge on exact current fee amounts / refund slabs / circular dates if those figures were not provided — then ask which programme and point to iiitdmj.ac.in.
- For a faculty email you are not sure of, give the directory link http://faculty.iiitdmj.ac.in/ rather than a guessed inbox."""


def index_ready() -> bool:
    return store.index_stats()["ready"]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(x * x for x in b)) or 1e-9
    return dot / (na * nb)


def _parse_as_of(query: str) -> str | None:
    m = re.search(r"\b(20\d{2})\b", query)
    if not m:
        return None
    if re.search(r"\b(in|as of|during|year)\b", query.lower()) or "क्या था" in query:
        return f"{m.group(1)}-12-31"
    return None


def _doc_date(ch: dict) -> str | None:
    return ch.get("effective_from") or ch.get("last_updated")


def _clean(text: str, limit: int) -> str:
    t = re.sub(r"<[^>]+>", " ", text or "")
    t = re.sub(r"&nbsp;|&amp;|&quot;", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:limit]


def _is_hindi(query: str) -> bool:
    return bool(re.search(r"[\u0900-\u097F]", query))


def detect_intent(query: str) -> Intent:
    q = query.lower()
    if re.search(r"refund|वापसी|रिफंड|withdraw|cancellation", q):
        return "refund"
    if re.search(r"fee|fees|शुल्क|फीस|tuition|mess advance|hostel fee", q):
        return "fee"
    if re.search(r"attend|attendance|एटेंडेंस|उपस्थिति|हाजिरी|dugc|shortfall", q):
        return "attendance"
    if re.search(r"hostel|हॉस्टल|हॉस्टेल|छात्रावास|warden", q):
        return "hostel"
    if re.search(
        r"\bhow is\b|\babout\b|established|what is iiitdm|संस्थान|के बारे में",
        q,
    ):
        return "about"
    return "general"


def fee_program(query: str) -> str | None:
    q = query.lower()
    if re.search(r"\bphd\b|doctoral|पीएचडी|पीएच\.?\s*डी", q):
        return "phd"
    if re.search(
        r"\bug\b|b\.?\s*tech|b\.?\s*des|undergraduate|btech|bdes|स्नातक|बी\.?\s*टेक|बीटेक",
        q,
    ):
        return "ug"
    if re.search(r"\bpg\b|m\.?\s*tech|mtech|postgraduate|स्नातकोत्तर|एम\.?\s*टेक", q):
        return "pg"
    return None


def _boost(doc_id: str, intent: Intent) -> float:
    did = (doc_id or "").lower()
    if intent == "fee":
        if did.startswith("fee-"):
            return 0.12
        if "faq" in did:
            return -0.04
        if "hostel" in did:
            return -0.06
    if intent == "refund" and ("refund" in did or "faq" in did):
        return 0.1
    if intent == "attendance" and "guideline" in did:
        return 0.08
    if intent == "hostel" and "hostel" in did:
        return 0.1
    return 0.0


def _search_queries(query: str, intent: Intent) -> list[str]:
    """Expand multi-part / casual questions into focused retrieval queries."""
    base = _retrieval_query(query)
    extras: list[str] = []
    if intent == "fee":
        prog = fee_program(query)
        if prog == "phd":
            extras.append("IIITDM Jabalpur PhD fee structure semester tuition hostel mess")
        elif prog == "ug":
            extras.append("IIITDM Jabalpur B.Tech B.Des UG fee structure tuition hostel")
        else:
            extras.append("IIITDM Jabalpur fee structure UG B.Tech PhD tuition")
    elif intent == "refund":
        extras.append("IIITDM Jabalpur refund rule admission withdrawal")
    elif intent == "attendance":
        extras.append("IIITDM Jabalpur attendance requirement end semester examination")
    # Drop fluff like "hey how is" for fee-focused retrieval
    if intent == "fee" and re.search(r"fee", query, re.I):
        extras.insert(0, "fee structure " + (fee_program(query) or "undergraduate postgraduate phd"))
    out = [base] + extras
    # unique preserve order
    seen: set[str] = set()
    uniq: list[str] = []
    for q in out:
        k = q.strip().lower()
        if k and k not in seen:
            seen.add(k)
            uniq.append(q.strip())
    return uniq[:3]


def retrieve(query: str, k: int = 8, intent: Intent | None = None) -> list[dict]:
    intent = intent or detect_intent(query)
    chunks = store.chunks()
    if not chunks:
        return []
    as_of = _parse_as_of(query)
    pool = chunks
    if as_of:
        filtered = [ch for ch in chunks if (d := _doc_date(ch)) and str(d) <= as_of]
        if filtered:
            pool = filtered

    # Prefer fee docs in pool when asking fees
    if intent == "fee":
        prog = fee_program(query)
        preferred = []
        for ch in pool:
            did = (ch.get("document_id") or "").lower()
            if prog == "phd" and did.startswith("fee-phd"):
                preferred.append(ch)
            elif prog == "ug" and did.startswith("fee-ug"):
                preferred.append(ch)
            elif not prog and did.startswith("fee-"):
                preferred.append(ch)
        if preferred:
            pool = preferred + [c for c in pool if c not in preferred]

    embeds = store.embeddings()
    best: dict[str, tuple[float, dict]] = {}

    queries = _search_queries(query, intent)
    if embeds and aimlapi.client():
        q_embs = aimlapi.embed_texts(queries)
        for q_emb in q_embs:
            for ch in pool:
                emb = embeds.get(ch["id"])
                if not emb:
                    continue
                score = cosine(q_emb, emb) + _boost(ch.get("document_id") or "", intent)
                prev = best.get(ch["id"])
                if not prev or score > prev[0]:
                    best[ch["id"]] = (score, ch)
        ranked = sorted(best.values(), key=lambda x: x[0], reverse=True)
        good = [c for s, c in ranked if s >= _MIN_COSINE][:k]
        if good:
            return _dedupe_docs(good, _MAX_SOURCES + 2)

    tokens = set(re.findall(r"[a-zA-Z0-9\u0900-\u097F]{3,}", query.lower()))
    scored_kw: list[tuple[float, dict]] = []
    for ch in pool:
        text = ch.get("text", "").lower()
        score = float(sum(1 for t in tokens if t in text)) + _boost(ch.get("document_id") or "", intent) * 10
        scored_kw.append((score, ch))
    scored_kw.sort(key=lambda x: x[0], reverse=True)
    good = [c for s, c in scored_kw if s >= _MIN_KEYWORD][:k]
    return _dedupe_docs(good, _MAX_SOURCES + 2)


def _dedupe_docs(hits: list[dict], limit: int) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for ch in hits:
        did = ch.get("document_id") or ch.get("id") or ""
        if did in seen:
            continue
        seen.add(did)
        out.append(ch)
        if len(out) >= limit:
            break
    return out


def _fee_tables(prog: str | None) -> list[dict]:
    all_t = store.tables()
    if prog == "phd":
        ids = {"fee-phd-2025"}
    elif prog == "ug":
        ids = {"fee-ug-2024"}
    else:
        ids = {"fee-ug-2024", "fee-phd-2025"}
    hits = [t for t in all_t if t.get("document_id") in ids]
    # Prefer one useful table per doc
    picked: list[dict] = []
    seen: set[str] = set()
    for t in hits:
        did = t.get("document_id") or ""
        if did in seen:
            continue
        seen.add(did)
        picked.append(t)
        if len(picked) >= 2:
            break
    return picked


def _source_cards(hits: list[dict]) -> tuple[list[dict], list[str]]:
    sources: list[dict] = []
    context_parts: list[str] = []
    for i, ch in enumerate(hits[:_MAX_SOURCES], start=1):
        sources.append(
            {
                "n": i,
                "title": ch.get("title") or ch.get("document_id") or "document",
                "url": ch.get("url") or "",
                "page": ch.get("page"),
                "excerpt": _clean(ch.get("text") or "", _EXCERPT_UI),
                "effective_from": ch.get("effective_from"),
                "last_updated": ch.get("last_updated"),
                "document_id": ch.get("document_id"),
            }
        )
        context_parts.append(
            f"[{i}] {ch.get('title')} | {ch.get('document_id')} | page={ch.get('page')} | "
            f"as_of={ch.get('effective_from')}\n{_clean(ch.get('text') or '', _EXCERPT_CTX)}"
        )
    return sources, context_parts


def _open_answer(query: str) -> dict:
    lang = "Hindi" if _is_hindi(query) else "the same language as the student"
    text = aimlapi.chat_completion(
        SYSTEM_OPEN,
        (
            f"Student question: {query}\nReply in {lang}.\n\n"
            f"Campus facts you may use:\n{campus_facts.FACTS}"
        ),
        temperature=0.35,
        max_tokens=480,
        model=settings.aimlapi_chat_model,
    )
    return {
        "text": text,
        "sources": [],
        "structures": [],
        "freshness": None,
        "contradiction": None,
        "mode": "open",
    }


def _use_open(query: str, intent: Intent) -> bool:
    if intent not in {"fee", "refund", "attendance", "hostel"}:
        return True
    return bool(
        re.search(
            r"\bdirector\b|\bregistrar\b|who is|who'?s\b|निदेशक|डायरेक्टर|कौन",
            query,
            re.I,
        )
    )


def answer(query: str) -> dict:
    if faculty.looks_like_faculty_query(query):
        rows = faculty.lookup(query)
        if rows:
            return {
                "text": faculty.format_answer(rows, query),
                "sources": faculty.source_cards(rows),
                "structures": [],
                "freshness": None,
                "contradiction": None,
                "mode": "faculty",
            }

    intent = detect_intent(query)
    prog = fee_program(query) if intent == "fee" else None
    if _use_open(query, intent) and not (intent == "fee" and not prog):
        if not aimlapi.client():
            return {
                "text": "AIMLAPI_KEY missing — cannot generate.",
                "sources": [],
                "structures": [],
                "freshness": None,
                "contradiction": None,
                "mode": "error",
            }
        return _open_answer(query)

    hits = retrieve(query, k=8, intent=intent)

    # Fee with no program → clarify first (still attach short fee-doc citations if present)
    if intent == "fee" and not prog:
        fee_hits = [
            c
            for c in store.chunks()
            if (c.get("document_id") or "").startswith("fee-")
        ]
        # one chunk per fee doc
        clarify_hits = _dedupe_docs(fee_hits, 2) or hits[:2]
        sources, _ = _source_cards(clarify_hits)
        structures = _fee_tables(None)
        if _is_hindi(query):
            text = (
                "किस कार्यक्रम की फीस चाहिए?\n"
                "• **UG** (B.Tech / B.Des)\n"
                "• **PhD**\n"
                "• **PG** (M.Tech / अन्य — बताएँ)\n\n"
                "कार्यक्रम लिखें, फिर आधिकारिक परिपत्र से रकम बताऊँगा"
                + (" और टेबल दिखाऊँगा।" if structures else "।")
            )
        else:
            text = (
                "Which programme’s fees do you need?\n"
                "• **UG** (B.Tech / B.Des)\n"
                "• **PhD**\n"
                "• **PG** (if you mean M.Tech / other PG — say which)\n\n"
                "Reply with the programme and I’ll quote the official amounts from the fee circular"
                + (" and show the table." if structures else ".")
            )
        if sources:
            text += " Fee circulars on file: " + ", ".join(f"[{s['n']}] {s['title']}" for s in sources) + "."
        return {
            "text": text,
            "sources": sources,
            "structures": [],  # wait until they pick a programme
            "freshness": None,
            "contradiction": None,
            "mode": "clarify",
        }

    policy = intent in {"fee", "refund", "attendance", "hostel"}
    leadership = bool(
        re.search(
            r"\bdirector\b|\bregistrar\b|\bdean\b|who is|who'?s\b|निदेशक|डायरेक्टर|कौन",
            query,
            re.I,
        )
    )
    open_mode = (not hits) or (not policy) or leadership
    sources, context_parts = _source_cards(hits)

    doc_ids = [h.get("document_id") for h in hits if h.get("document_id")]
    if intent == "fee" and prog:
        structures = _fee_tables(prog)
        # Ensure fee doc is in sources if table exists
        if structures and not any((d or "").startswith("fee-") for d in doc_ids):
            extra = [
                c
                for c in store.chunks()
                if (c.get("document_id") or "")
                == ("fee-phd-2025" if prog == "phd" else "fee-ug-2024")
            ]
            if extra:
                hits = _dedupe_docs(extra + hits, _MAX_SOURCES)
                sources, context_parts = _source_cards(hits)
                doc_ids = [h.get("document_id") for h in hits if h.get("document_id")]
    else:
        structures = [] if open_mode else extract.tables_for_docs(doc_ids, limit=2)

    freshness = None
    dates = [str(d) for d in (_doc_date(h) for h in hits) if d]
    if dates:
        freshness = {"asOf": max(dates), "lastUpdated": max(dates)}
    as_of = _parse_as_of(query)
    if as_of and not open_mode:
        freshness = {"asOf": as_of[:4], "lastUpdated": max(dates) if dates else as_of}

    contra_card = None
    if not open_mode:
        contra_item = conflict.match_seeded(query, doc_ids)
        if contra_item:
            contra_card = conflict.to_card(contra_item, hits)
        else:
            judged = conflict.judge_hits(query, hits)
            if judged:
                contra_card = conflict.to_card(judged, hits)

    if not aimlapi.client():
        return {
            "text": "AIMLAPI_KEY missing — cannot generate.",
            "sources": sources,
            "structures": structures,
            "freshness": freshness,
            "contradiction": contra_card,
            "mode": "error",
        }

    grounded_model = getattr(settings, "aimlapi_grounded_model", None) or settings.aimlapi_chat_model

    if open_mode:
        return _open_answer(query)

    table_note = ""
    if structures:
        table_note = "\n\nOfficial fee/refund tables (use these numbers; UI will show the table):\n"
        table_note += str(
            [
                {
                    "title": s.get("title"),
                    "document_id": s.get("document_id"),
                    "page": s.get("page"),
                    "rows": s.get("rows", [])[:12],
                }
                for s in structures
            ]
        )

    focus = {
        "fee": "Focus on fee amounts for the named programme. Skip institute history.",
        "refund": "Focus on refund / withdrawal amounts and windows.",
        "attendance": "Focus on the attendance % / exam eligibility rule.",
        "hostel": "Focus on hostel rules or hostel fee if asked.",
        "about": "One short factual blurb about the institute is OK, then stop.",
        "general": "Answer the question directly.",
    }[intent]

    lang = "Reply in Hindi." if _is_hindi(query) else "Reply in the student’s language."
    user = (
        f"Student question: {query}\n"
        f"Intent: {intent}\n"
        f"Instruction: {focus}\n"
        f"{lang}\n"
        "If the sources below do not answer the question, still answer from campus facts "
        "and your knowledge. Never say the sources are missing the answer.\n\n"
        f"Campus facts:\n{campus_facts.FACTS}\n\n"
        f"Sources:\n\n" + "\n\n".join(context_parts) + table_note
    )
    if contra_card:
        user += f"\n\nDisagreement to surface briefly: {contra_card.get('claim')}"

    text = aimlapi.chat_completion(
        SYSTEM_GROUNDED,
        user,
        temperature=0.15,
        max_tokens=420,
        model=grounded_model,
    )
    return {
        "text": text,
        "sources": sources,
        "structures": structures[:1] if intent == "fee" else structures[:2],
        "freshness": freshness,
        "contradiction": contra_card,
        "mode": "grounded",
    }


def _retrieval_query(query: str) -> str:
    # Strip chatty prefixes
    q = re.sub(r"^(hey|hi|hello|hii)[,\s]+", "", query.strip(), flags=re.I)
    if re.search(r"[\u0900-\u097F]", q) and aimlapi.client():
        try:
            return aimlapi.chat_completion(
                "Rewrite as a short English search query for college policy PDFs. Output only the query.",
                q,
                temperature=0,
                max_tokens=40,
            )
        except Exception:  # noqa: BLE001
            return q
    return q
