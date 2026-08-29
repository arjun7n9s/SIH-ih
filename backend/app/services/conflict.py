"""Contradiction surfacing: seeded pairs + optional LLM judge on retrieved hits."""

from __future__ import annotations

import json
import re

from app.services import aimlapi, store


def list_seeded() -> list[dict]:
    return store.contradictions_seed()


def match_seeded(query: str, hit_doc_ids: list[str]) -> dict | None:
    q = query.lower()
    docs = set(hit_doc_ids)
    for item in store.contradictions_seed():
        triggers = [t.lower() for t in item.get("triggers", [])]
        doc_a = item.get("doc_a")
        doc_b = item.get("doc_b")
        triggered = any(t in q for t in triggers) if triggers else False
        both_retrieved = doc_a in docs and doc_b in docs
        if triggered or both_retrieved:
            return item
    return None


def judge_hits(query: str, hits: list[dict]) -> dict | None:
    """Ask AIMLAPI whether top hits contradict; return structured pair or None."""
    if len(hits) < 2 or not aimlapi.client():
        return None
    payload = []
    for i, h in enumerate(hits[:4], start=1):
        payload.append(
            {
                "n": i,
                "document_id": h.get("document_id"),
                "title": h.get("title"),
                "page": h.get("page"),
                "text": (h.get("text") or "")[:600],
                "effective_from": h.get("effective_from"),
            }
        )
    prompt = (
        "Do any two sources contradict on a concrete policy/fee/date fact for this question?\n"
        f"Question: {query}\n"
        f"Sources JSON: {json.dumps(payload, ensure_ascii=False)}\n"
        'If yes, reply ONLY JSON: {"claim":"...","a_n":1,"b_n":2,"note":"..."}\n'
        'If no, reply ONLY: {"claim":null}'
    )
    try:
        raw = aimlapi.chat_completion(
            "You detect contradictions in college policy sources. JSON only.",
            prompt,
        )
        m = re.search(r"\{.*\}", raw, re.S)
        if not m:
            return None
        data = json.loads(m.group(0))
        if not data.get("claim"):
            return None
        a = next((h for i, h in enumerate(hits, 1) if i == data.get("a_n")), hits[0])
        b = next((h for i, h in enumerate(hits, 1) if i == data.get("b_n")), hits[1])
        return {
            "claim": data["claim"],
            "note": data.get("note", ""),
            "a": a,
            "b": b,
        }
    except Exception:  # noqa: BLE001
        return None


def to_card(item: dict, hits: list[dict] | None = None) -> dict:
    """Normalize seed or judged item into SSE contradiction payload."""
    if "a" in item and isinstance(item["a"], dict) and "excerpt" in item.get("a", {}):
        return {
            "type": "contradiction",
            "claim": item["claim"],
            "a": item["a"],
            "b": item["b"],
        }

    def side(doc_id: str, key: str) -> dict:
        seed_side = item.get(key, {})
        hit = next((h for h in (hits or []) if h.get("document_id") == doc_id), None)
        return {
            "n": 1 if key == "side_a" else 2,
            "title": seed_side.get("title") or (hit or {}).get("title") or doc_id,
            "url": seed_side.get("url") or (hit or {}).get("url") or "",
            "page": seed_side.get("page") or (hit or {}).get("page"),
            "excerpt": seed_side.get("excerpt")
            or ((hit or {}).get("text") or "")[:280],
            "effective_from": seed_side.get("effective_from")
            or (hit or {}).get("effective_from"),
        }

    if "doc_a" in item:
        a = side(item["doc_a"], "side_a")
        b = side(item["doc_b"], "side_b")
        a["n"], b["n"] = 1, 2
        return {"type": "contradiction", "claim": item["claim"], "a": a, "b": b}

    # judged shape with raw hits
    a_hit, b_hit = item["a"], item["b"]
    return {
        "type": "contradiction",
        "claim": item["claim"],
        "a": {
            "n": 1,
            "title": a_hit.get("title") or a_hit.get("document_id"),
            "url": a_hit.get("url") or "",
            "page": a_hit.get("page"),
            "excerpt": (a_hit.get("text") or "")[:280],
            "effective_from": a_hit.get("effective_from"),
        },
        "b": {
            "n": 2,
            "title": b_hit.get("title") or b_hit.get("document_id"),
            "url": b_hit.get("url") or "",
            "page": b_hit.get("page"),
            "excerpt": (b_hit.get("text") or "")[:280],
            "effective_from": b_hit.get("effective_from"),
        },
    }
