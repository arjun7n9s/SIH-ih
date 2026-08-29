from fastapi import APIRouter

from app.fixtures.demo import DEMO

router = APIRouter(prefix="/api", tags=["contradictions"])


@router.get("/contradictions")
async def list_contradictions() -> dict:
    cards = []
    for key in ("attendance", "refund"):
        for event in DEMO[key]:
            if event.get("type") == "contradiction":
                cards.append(event)
    return {"items": cards}
