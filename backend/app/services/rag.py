"""Lightweight JSONL RAG — no Chroma yet. Cosine over AIMLAPI embeddings."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

from app.services import aimlapi

REPO = Path(__file__).resolve().parents[3]
CHUNKS = REPO / "data" / "index" / "chunks.jsonl"
EMBEDS = REPO / "data" / "index" / "embeddings.jsonl"

SYSTEM = """You are Suchna, the IIITDM Jabalpur knowledge assistant.
Answer ONLY from the provided sources. Cite as [1], [2].
If sources disagree, say so clearly and present both.
If the user wrote Hindi/Hinglish, answer in the same language.
Keep answers tight and student-useful. Never invent fees or rules."""


def index_ready() -> bool:
    return CHUNKS.exists() and CHUNKS.stat().st_size > 0


def load_chunks(limit: int | None = None) -> list[dict]:
    if not index_ready():
        return []
    rows: list[dict] = []
    with CHUNKS.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
            if limit and len(rows) >= limit:
                break
    return rows


def load_embeddings() -> dict[str, list[float]]:
    if not EMBEDS.exists():
        return {}
    out: dict[str, list[float]] = {}
    with EMBEDS.open(encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            out[row["id"]] = row["embedding"]
    return out


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(x * x for x in b)) or 1e-9
    return dot / (na * nb)


def retrieve(query: str, k: int = 5) -> list[dict]:
    chunks = load_chunks()
    if not chunks:
        return []
    embeds = load_embeddings()
    if embeds and aimlapi.client():
        q_emb = aimlapi.embed_texts([_retrieval_query(query)])
        if q_emb:
            scored = []
            for ch in chunks:
                emb = embeds.get(ch["id"])
                if not emb:
                    continue
                scored.append((cosine(q_emb[0], emb), ch))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [c for _, c in scored[:k]]
    # lexical fallback
    tokens = set(re.findall(r"[a-zA-Z0-9\u0900-\u097F]{3,}", query.lower()))
    scored = []
    for ch in chunks:
        text = ch.get("text", "").lower()
        score = sum(1 for t in tokens if t in text)
        scored.append((score, ch))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for s, c in scored[:k] if s > 0] or [c for _, c in scored[:k]]


def answer(query: str) -> dict:
    hits = retrieve(query, k=5)
    sources = []
    context_parts = []
    for i, ch in enumerate(hits, start=1):
        sources.append(
            {
                "n": i,
                "title": ch.get("document_id", "document"),
                "url": ch.get("url") or "",
                "page": ch.get("page"),
                "excerpt": (ch.get("text") or "")[:280],
                "effective_from": ch.get("effective_from"),
                "last_updated": ch.get("last_updated"),
            }
        )
        context_parts.append(
            f"[{i}] doc={ch.get('document_id')} page={ch.get('page')}\n{ch.get('text', '')}"
        )
    if not aimlapi.client():
        return {
            "text": "AIMLAPI_KEY is set for the server? Retrieval found sources but generation is unavailable.",
            "sources": sources,
        }
    user = f"Question: {query}\n\nSources:\n\n" + "\n\n".join(context_parts)
    text = aimlapi.chat_completion(SYSTEM, user)
    return {"text": text, "sources": sources}


def _retrieval_query(query: str) -> str:
    # Hindi/Hinglish → English retrieval hint via LLM when available
    if re.search(r"[\u0900-\u097F]", query) and aimlapi.client():
        try:
            return aimlapi.chat_completion(
                "Translate to a short English search query for college policy documents. Output only the query.",
                query,
            )
        except Exception:  # noqa: BLE001
            return query
    return query
