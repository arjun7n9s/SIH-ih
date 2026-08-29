from __future__ import annotations

import yaml
from fastapi import APIRouter

from app.services import extract, store

router = APIRouter(prefix="/api", tags=["corpus"])


@router.get("/documents")
async def list_documents() -> dict:
    path = store.MANIFEST_PATH
    if not path.exists():
        return {"items": []}
    docs = yaml.safe_load(path.read_text(encoding="utf-8")).get("documents", [])
    items = []
    for d in docs:
        items.append(
            {
                "id": d.get("id"),
                "title": d.get("title"),
                "url": d.get("url"),
                "type": d.get("type"),
                "effective_from": str(d.get("effective_from") or ""),
                "last_updated": str(d.get("last_updated") or ""),
                "demo": bool(d.get("demo")),
            }
        )
    return {"count": len(items), "items": items}


@router.get("/extract")
async def list_extracted() -> dict:
    tables = store.tables()
    return {"count": len(tables), "items": tables}


@router.post("/extract/rebuild")
async def rebuild_extracted() -> dict:
    cards = extract.build_tables()
    store.clear_cache()
    return {"count": len(cards), "items": cards}
