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

SYSTEM_RAG = """You are Suchna’s corpus reader for PDPM IIITDM Jabalpur.

Answer ONLY from the official passages, fee tables, and faculty directory block.
Cite as [1], [2] when you use a passage. Be short. No preamble.
English by default; Hindi only if told to.
If the files do not contain the fact, say exactly: CORPUS_MISS
Do not invent fee amounts or faculty emails."""

SYSTEM_GEMINI = """You are Suchna’s general campus tutor for PDPM IIITDM Jabalpur (Gemini).

Answer the student directly from your knowledge plus any campus facts / directory given.
English by default; Hindi only if told to. No preamble.
Always give a useful answer. Never say you lack context.
Do not invent exact current fee circular dates if none were provided."""

SYSTEM_JUDGE = """You are Suchna’s final editor. You see two drafts and the evidence.

Draft A = RAG / official corpus + faculty directory.
Draft B = Gemini general knowledge.

Write ONE student-facing answer. Do not mention drafts, models, RAG, or that you judged.

Rules:
- Fees, refunds, attendance, circular dates: prefer A when it has real figures. Never average two different rupee amounts.
- Faculty email, phone, research: prefer A if it quotes the directory. Use B only to fill a gap A left empty.
- Director, campus life, how-to, general: prefer B if A is CORPUS_MISS or thin; merge extra true facts from both.
- Follow-ups refer to earlier chat. English default; Hindi only if the latest message has Devanagari.
- Never say “no context”, “not in the sources”, or CORPUS_MISS to the student.
- If a programme is still unnamed for fees, ask UG / PhD / PG."""


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
    """True only when the latest message has Devanagari — not Hinglish in Latin letters."""
    return bool(re.search(r"[\u0900-\u097F]", query or ""))


def _is_followup(query: str) -> bool:
    q = (query or "").strip()
    words = re.findall(r"[a-zA-Z0-9\u0900-\u097F]+", q)
    if len(words) <= 6:
        return True
    return bool(
        re.match(
            r"^(and|also|what about|how about|his|her|their|that|those|this|"
            r"yes|ok|okay|ug|phd|pg|b\.?\s*tech)\b",
            q,
            re.I,
        )
    )


def _blend_query(query: str, history: list[dict] | None) -> str:
    if not history or not _is_followup(query):
        return query
    prior = [m.get("content") or "" for m in history if (m.get("role") or "") == "user"]
    if not prior:
        return query
    return f"{prior[-1].strip()} — {query.strip()}"


def _history_block(history: list[dict] | None) -> str:
    if not history:
        return ""
    lines: list[str] = []
    for m in history[-8:]:
        role = "Student" if m.get("role") == "user" else "Suchna"
        content = (m.get("content") or "").strip()[:800]
        if content:
            lines.append(f"{role}: {content}")
    if not lines:
        return ""
    return "Earlier in this chat:\n" + "\n".join(lines) + "\n\n"


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


def _clarify_fees(query: str, hits: list[dict]) -> dict:
    fee_hits = [c for c in store.chunks() if (c.get("document_id") or "").startswith("fee-")]
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
        "structures": [],
        "freshness": None,
        "contradiction": None,
        "mode": "clarify",
    }


def answer(query: str, history: list[dict] | None = None) -> dict:
    lookup_q = _blend_query(query, history)
    intent = detect_intent(lookup_q)
    prog = fee_program(lookup_q) if intent == "fee" else fee_program(query)
    policy = intent in {"fee", "refund", "attendance", "hostel"}

    if intent == "fee" and not prog:
        return _clarify_fees(query, [])

    hits: list[dict] = []
    try:
        hits = retrieve(lookup_q, k=8, intent=intent)
    except Exception:  # noqa: BLE001
        hits = []

    sources, context_parts = _source_cards(hits)
    doc_ids = [h.get("document_id") for h in hits if h.get("document_id")]
    structures: list[dict] = []
    if intent == "fee" and prog:
        structures = _fee_tables(prog)
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
    elif policy and hits:
        structures = extract.tables_for_docs(doc_ids, limit=2)

    freshness = None
    dates = [str(d) for d in (_doc_date(h) for h in hits) if d]
    if dates:
        freshness = {"asOf": max(dates), "lastUpdated": max(dates)}

    contra_card = None
    if policy and hits:
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

    fac_rows = faculty.lookup(lookup_q) or faculty.lookup(query)
    fac_like = faculty.looks_like_faculty_query(lookup_q) or faculty.looks_like_faculty_query(query)
    directory = ""
    if fac_like:
        directory = (
            faculty.format_answer(fac_rows, query)
            if fac_rows
            else faculty.directory_prompt()
        )
    table_note = ""
    if structures:
        table_note = "\n\nOfficial fee/refund tables (use these numbers):\n" + str(
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

    lang = "Hindi (Devanagari)" if _is_hindi(query) else "English"
    shared = (
        f"{_history_block(history)}"
        f"Latest student message: {query}\n"
        f"Resolved question: {lookup_q}\n"
        f"Reply in {lang} only.\n"
    )
    evidence = f"Campus facts:\n{campus_facts.FACTS}\n"
    if directory:
        evidence += f"\nFaculty directory hit:\n{directory}\n"
    if context_parts:
        evidence += "\nOfficial passages:\n\n" + "\n\n".join(context_parts)
    evidence += table_note
    if contra_card:
        evidence += f"\n\nCorpus disagreement: {contra_card.get('claim')}"

    rag_user = (
        shared
        + "\nUse ONLY the evidence below. If it does not answer the question, output CORPUS_MISS.\n\n"
        + evidence
    )
    gemini_user = (
        shared
        + "\nAnswer helpfully. Evidence below may help; you may also use general knowledge.\n\n"
        + evidence
    )

    rag_model = getattr(settings, "aimlapi_grounded_model", None) or "gpt-4o"
    gemini_model = settings.aimlapi_chat_model
    judge_model = getattr(settings, "aimlapi_judge_model", None) or "gpt-4o-mini"

    rag_text, gemini_text = aimlapi.complete_parallel(
        [
            {
                "system": SYSTEM_RAG,
                "user": rag_user,
                "model": rag_model,
                "temperature": 0.1,
                "max_tokens": 420,
            },
            {
                "system": SYSTEM_GEMINI,
                "user": gemini_user,
                "model": gemini_model,
                "temperature": 0.35,
                "max_tokens": 480,
            },
        ]
    )
    if fac_rows and (not rag_text or rag_text.strip() == "CORPUS_MISS"):
        rag_text = faculty.format_answer(fac_rows, query)

    judge_user = (
        shared
        + f"\n--- Draft A (RAG / corpus) ---\n{rag_text or '(empty)'}\n"
        + f"\n--- Draft B (Gemini) ---\n{gemini_text or '(empty)'}\n"
        + f"\n--- Evidence ---\n{evidence}\n"
        + "\nWrite the final answer for the student now."
    )
    text = aimlapi.chat_completion_safe(
        SYSTEM_JUDGE,
        judge_user,
        temperature=0.15,
        max_tokens=520,
        model=judge_model,
    )
    if not text:
        text = rag_text if rag_text and "CORPUS_MISS" not in rag_text else gemini_text
    if not text:
        text = "Couldn’t finish that just now — ask once more."

    fac_sources = faculty.source_cards(fac_rows) if fac_rows else []
    return {
        "text": text,
        "sources": sources or fac_sources,
        "structures": structures[:1] if intent == "fee" else structures[:2],
        "freshness": freshness,
        "contradiction": contra_card,
        "mode": "ensemble",
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
