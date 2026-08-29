"""JSONL RAG with structures, freshness, and contradiction cards."""

from __future__ import annotations

import math
import re

from app.services import aimlapi, conflict, extract, store

SYSTEM = """You are Suchna, the IIITDM Jabalpur knowledge assistant.
Answer ONLY from the provided sources. Cite as [1], [2].
If sources disagree, say so clearly and present both — do not pick a silent winner.
If the user wrote Hindi/Hinglish, answer in the same language.
Keep answers tight and student-useful. Never invent fees or rules.
When a structured table is provided separately, you may refer to it but still cite sources."""


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
            scored = []
            for ch in pool:
                emb = embeds.get(ch["id"])
                if not emb:
                    continue
                scored.append((cosine(q_emb[0], emb), ch))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [c for _, c in scored[:k]]

    tokens = set(re.findall(r"[a-zA-Z0-9\u0900-\u097F]{3,}", query.lower()))
    scored = []
    for ch in pool:
        text = ch.get("text", "").lower()
        score = sum(1 for t in tokens if t in text)
        scored.append((score, ch))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for s, c in scored[:k] if s > 0] or [c for _, c in scored[:k]]


def answer(query: str) -> dict:
    hits = retrieve(query, k=6)
    sources = []
    context_parts = []
    for i, ch in enumerate(hits, start=1):
        sources.append(
            {
                "n": i,
                "title": ch.get("title") or ch.get("document_id") or "document",
                "url": ch.get("url") or "",
                "page": ch.get("page"),
                "excerpt": (ch.get("text") or "")[:280],
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
    structures = extract.tables_for_docs(doc_ids, limit=2)

    freshness = None
    dates = [str(d) for d in (_doc_date(h) for h in hits) if d]
    if dates:
        freshness = {
            "asOf": max(dates),
            "lastUpdated": max(dates),
        }
    as_of = _parse_as_of(query)
    if as_of:
        freshness = {"asOf": as_of[:4], "lastUpdated": max(dates) if dates else as_of}

    contra_item = conflict.match_seeded(query, doc_ids)
    contra_card = None
    if contra_item:
        contra_card = conflict.to_card(contra_item, hits)
    else:
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
        }

    table_note = ""
    if structures:
        table_note = "\n\nStructured tables available to the UI (do not invent numbers):\n"
        table_note += str(
            [
                {"title": s.get("title"), "document_id": s.get("document_id"), "rows": s.get("rows", [])[:8]}
                for s in structures
            ]
        )

    user = f"Question: {query}\n\nSources:\n\n" + "\n\n".join(context_parts) + table_note
    if contra_card:
        user += f"\n\nKnown disagreement: {contra_card.get('claim')}. Surface both sides."
    text = aimlapi.chat_completion(SYSTEM, user)
    return {
        "text": text,
        "sources": sources,
        "structures": structures,
        "freshness": freshness,
        "contradiction": contra_card,
    }


def _retrieval_query(query: str) -> str:
    if re.search(r"[\u0900-\u097F]", query) and aimlapi.client():
        try:
            return aimlapi.chat_completion(
                "Translate to a short English search query for college policy documents. Output only the query.",
                query,
            )
        except Exception:  # noqa: BLE001
            return query
    return query
