from fastapi import APIRouter

from app.services import conflict, store

router = APIRouter(prefix="/api", tags=["contradictions"])


@router.get("/contradictions")
async def list_contradictions() -> dict:
    items = []
    for seed in conflict.list_seeded():
        items.append(conflict.to_card(seed))
    return {"count": len(items), "items": items}


@router.get("/contradictions/{item_id}")
async def get_contradiction(item_id: str) -> dict:
    for seed in conflict.list_seeded():
        if seed.get("id") == item_id:
            return conflict.to_card(seed)
    return {"error": "not_found", "id": item_id}
