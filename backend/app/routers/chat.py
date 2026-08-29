from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.config import settings
from app.fixtures.demo import pick_demo
from app.models.schema import ChatRequest
from app.services import rag

router = APIRouter(prefix="/api", tags=["chat"])


def _sse(event: dict) -> bytes:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n".encode("utf-8")


@router.post("/chat")
async def chat(body: ChatRequest) -> StreamingResponse:
    use_live = (
        not settings.use_mock
        and bool(settings.aimlapi_key)
        and rag.index_ready()
    )

    async def gen_mock():
        for event in pick_demo(body.query):
            yield _sse(event)
            await asyncio.sleep(0.02)

    async def gen_live():
        yield _sse({"type": "status", "label": "Searching institute documents…"})
        await asyncio.sleep(0.01)
        try:
            result = await asyncio.to_thread(rag.answer, body.query)
        except Exception as err:  # noqa: BLE001
            yield _sse({"type": "token", "text": f"RAG error: {err}"})
            yield _sse({"type": "done"})
            return
        if result.get("sources"):
            sources = []
            for s in result["sources"]:
                sources.append(
                    {
                        **s,
                        "title": s.get("title") or s.get("document_id") or "source",
                    }
                )
            yield _sse({"type": "sources", "items": sources})
        text = result.get("text") or ""
        # stream in chunks for UI feel
        step = 80
        for i in range(0, len(text), step):
            yield _sse({"type": "token", "text": text[i : i + step]})
            await asyncio.sleep(0.01)
        yield _sse({"type": "done"})

    return StreamingResponse(
        gen_live() if use_live else gen_mock(),
        media_type="text/event-stream",
    )
