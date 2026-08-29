from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.config import settings
from app.fixtures.demo import pick_demo
from app.models.schema import ChatRequest

router = APIRouter(prefix="/api", tags=["chat"])


def _sse(event: dict) -> bytes:
    import json

    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n".encode("utf-8")


@router.post("/chat")
async def chat(body: ChatRequest) -> StreamingResponse:
    events = pick_demo(body.query)

    async def gen():
        for event in events:
            yield _sse(event)
        # Live RAG is Block C. Until AIMLAPI + index exist, mock is the product.
        if not settings.use_mock and settings.aimlapi_key:
            yield _sse(
                {
                    "type": "status",
                    "label": "Live RAG not wired yet — still on fixtures. Fill AIMLAPI_KEY and run index_corpus.py.",
                }
            )

    return StreamingResponse(gen(), media_type="text/event-stream")
