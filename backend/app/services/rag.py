"""JSONL RAG with structures, freshness, contradiction cards, and open fallback."""

from __future__ import annotations

import math
import re

from app.services import aimlapi, conflict, extract, store

# Cosine / keyword floors — below this we treat the index as a miss.
_MIN_COSINE = 0.28
_MIN_KEYWORD = 2

SYSTEM_GROUNDED = """You are Suchna, the IIITDM Jabalpur campus knowledge assistant.

Rules:
- Prefer the provided sources. Cite them as [1], [2].
- Be concise: usually 4–8 short sentences or a short bullet list. No filler, no preamble.
- If sources disagree, say so and present both — do not pick a silent winner.
- Match the user's language (English, Hindi, or Hinglish).
- Never invent specific fee amounts, dates, or clause numbers that are not in the sources.
- Ignore HTML tags / markup noise in sources; use only clear policy facts.
- When a structured table is provided separately, point the student to it instead of pasting huge tables.
- End only when the question is answered — no “hope this helps” closers."""

SYSTEM_OPEN = """You are Suchna, a helpful campus knowledge assistant for students (especially IIITDM Jabalpur context).

The campus document index did not return reliable sources for this question.

Rules:
- Answer helpfully from general knowledge and common Indian institute practice, like a careful tutor.
- Be concise: usually 4–8 short sentences or a short bullet list.
- Start with one clear line: you could not find this in the official campus index, so this is general guidance — verify on iiitdmj.ac.in or with the academic / hostel office before acting.
- Do NOT invent specific IIITDMJ fee figures, ordinance clause numbers, or “as per circular dated …” claims.
- If the topic is institute-specific policy, give the practical next step (which office / page to check).
- Match the user's language (English, Hindi, or Hinglish).
- No filler, no long essays."""


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


def retrieve(query: str, k: int = 6) -> list[dict]:
    """Return strong hits only. Empty list means open / general mode."""
    chunks = store.chunks()
    if not chunks:
        return []
    as_of = _parse_as_of(query)
    pool = chunks
    if as_of:
        filtered = []
        for ch in chunks:
            d = _doc_date(ch)
            if d and str(d) <= as_of:
                filtered.append(ch)
        if filtered:
            pool = filtered

    embeds = store.embeddings()
    q_text = _retrieval_query(query)
    if embeds and aimlapi.client():
        q_emb = aimlapi.embed_texts([q_text])
        if q_emb:
            scored: list[tuple[float, dict]] = []
            for ch in pool:
                emb = embeds.get(ch["id"])
                if not emb:
                    continue
                scored.append((cosine(q_emb[0], emb), ch))
            scored.sort(key=lambda x: x[0], reverse=True)
            good = [c for s, c in scored[:k] if s >= _MIN_COSINE]
            return good

    tokens = set(re.findall(r"[a-zA-Z0-9\u0900-\u097F]{3,}", query.lower()))
    scored_kw: list[tuple[float, dict]] = []
    for ch in pool:
        text = ch.get("text", "").lower()
        score = float(sum(1 for t in tokens if t in text))
        scored_kw.append((score, ch))
    scored_kw.sort(key=lambda x: x[0], reverse=True)
    good = [c for s, c in scored_kw[:k] if s >= _MIN_KEYWORD]
    return good


def answer(query: str) -> dict:
    hits = retrieve(query, k=6)
    open_mode = not hits

    sources = []
    context_parts = []
    for i, ch in enumerate(hits, start=1):
        excerpt = re.sub(r"<[^>]+>", " ", ch.get("text") or "")
        excerpt = re.sub(r"\s+", " ", excerpt).strip()[:280]
        sources.append(
            {
                "n": i,
                "title": ch.get("title") or ch.get("document_id") or "document",
                "url": ch.get("url") or "",
                "page": ch.get("page"),
                "excerpt": excerpt,
                "effective_from": ch.get("effective_from"),
                "last_updated": ch.get("last_updated"),
                "document_id": ch.get("document_id"),
            }
        )
        context_parts.append(
            f"[{i}] title={ch.get('title')} doc={ch.get('document_id')} "
            f"page={ch.get('page')} effective_from={ch.get('effective_from')}\n"
            f"{ch.get('text', '')}"
        )

    doc_ids = [h.get("document_id") for h in hits if h.get("document_id")]
    structures = [] if open_mode else extract.tables_for_docs(doc_ids, limit=2)

    freshness = None
    dates = [str(d) for d in (_doc_date(h) for h in hits) if d]
    if dates:
        freshness = {
            "asOf": max(dates),
            "lastUpdated": max(dates),
        }
    as_of = _parse_as_of(query)
    if as_of and not open_mode:
        freshness = {"asOf": as_of[:4], "lastUpdated": max(dates) if dates else as_of}

    contra_item = None if open_mode else conflict.match_seeded(query, doc_ids)
    contra_card = None
    if contra_item:
        contra_card = conflict.to_card(contra_item, hits)
    elif not open_mode:
        judged = conflict.judge_hits(query, hits)
        if judged:
            contra_card = conflict.to_card(judged, hits)

    if not aimlapi.client():
        return {
            "text": "AIMLAPI_KEY missing — cannot generate. Sources retrieved below.",
            "sources": sources,
            "structures": structures,
            "freshness": freshness,
            "contradiction": contra_card,
            "mode": "error",
        }

    if open_mode:
        user = (
            f"Student question: {query}\n\n"
            "No reliable campus-index passages were retrieved. "
            "Answer in open / general-guidance mode."
        )
        text = aimlapi.chat_completion(
            SYSTEM_OPEN,
            user,
            temperature=0.45,
            max_tokens=550,
        )
        return {
            "text": text,
            "sources": [],
            "structures": [],
            "freshness": None,
            "contradiction": None,
            "mode": "open",
        }

    table_note = ""
    if structures:
        table_note = "\n\nStructured tables available to the UI (do not invent numbers):\n"
        table_note += str(
            [
                {
                    "title": s.get("title"),
                    "document_id": s.get("document_id"),
                    "rows": s.get("rows", [])[:8],
                }
                for s in structures
            ]
        )

    user = f"Question: {query}\n\nSources:\n\n" + "\n\n".join(context_parts) + table_note
    if contra_card:
        user += f"\n\nKnown disagreement: {contra_card.get('claim')}. Surface both sides briefly."
    text = aimlapi.chat_completion(
        SYSTEM_GROUNDED,
        user,
        temperature=0.25,
        max_tokens=650,
    )
    return {
        "text": text,
        "sources": sources,
        "structures": structures,
        "freshness": freshness,
        "contradiction": contra_card,
        "mode": "grounded",
    }


def _retrieval_query(query: str) -> str:
    if re.search(r"[\u0900-\u097F]", query) and aimlapi.client():
        try:
            return aimlapi.chat_completion(
                "Translate to a short English search query for college policy documents. Output only the query.",
                query,
                temperature=0,
                max_tokens=48,
            )
        except Exception:  # noqa: BLE001
            return query
    return query
