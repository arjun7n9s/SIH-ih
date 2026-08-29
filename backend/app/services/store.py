"""In-memory index cache for low-latency retrieval."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
INDEX = REPO / "data" / "index"
CHUNKS_PATH = INDEX / "chunks.jsonl"
EMBEDS_PATH = INDEX / "embeddings.jsonl"
TABLES_PATH = INDEX / "tables.json"
CONTRA_PATH = REPO / "data" / "contradictions.seed.json"
MANIFEST_PATH = REPO / "data" / "corpus" / "manifest.yaml"


@lru_cache(maxsize=1)
def chunks() -> list[dict]:
    if not CHUNKS_PATH.exists():
        return []
    rows: list[dict] = []
    with CHUNKS_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


@lru_cache(maxsize=1)
def embeddings() -> dict[str, list[float]]:
    if not EMBEDS_PATH.exists():
        return {}
    out: dict[str, list[float]] = {}
    with EMBEDS_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            out[row["id"]] = row["embedding"]
    return out


@lru_cache(maxsize=1)
def tables() -> list[dict]:
    if not TABLES_PATH.exists():
        return []
    return json.loads(TABLES_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def contradictions_seed() -> list[dict]:
    if not CONTRA_PATH.exists():
        return []
    data = json.loads(CONTRA_PATH.read_text(encoding="utf-8"))
    return data.get("items", data if isinstance(data, list) else [])


def index_stats() -> dict:
    return {
        "chunks": len(chunks()),
        "embeddings": len(embeddings()),
        "tables": len(tables()),
        "contradictions": len(contradictions_seed()),
        "ready": CHUNKS_PATH.exists() and CHUNKS_PATH.stat().st_size > 0,
    }


def clear_cache() -> None:
    chunks.cache_clear()
    embeddings.cache_clear()
    tables.cache_clear()
    contradictions_seed.cache_clear()
