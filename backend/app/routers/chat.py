from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.config import settings
from app.fixtures.demo import pick_demo
from app.models.schema import ChatRequest, ChatSyncResponse
from app.services import rag

router = APIRouter(prefix="/api", tags=["chat"])


def _sse(event: dict) -> bytes:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n".encode("utf-8")


def _want_live(body: ChatRequest) -> bool:
    if body.mock is True:
        return False
    if body.mock is False:
        return bool(settings.aimlapi_key) and rag.index_ready()
    return (not settings.use_mock) and bool(settings.aimlapi_key) and rag.index_ready()


def _events_from_result(result: dict) -> list[dict]:
    events: list[dict] = []
    if result.get("freshness"):
        events.append({"type": "freshness", **result["freshness"]})
    if result.get("sources"):
        events.append({"type": "sources", "items": result["sources"]})
    for structure in result.get("structures") or []:
        events.append(
            {
                "type": "structure",
                "kind": structure.get("kind", "table"),
                "title": structure.get("title", "table"),
                "rows": structure.get("rows", []),
                "document_id": structure.get("document_id"),
                "page": structure.get("page"),
            }
        )
    text = result.get("text") or ""
    if text:
        events.append({"type": "token", "text": text})
    if result.get("contradiction"):
        events.append(result["contradiction"])
    events.append({"type": "done"})
    return events


@router.post("/chat")
async def chat_stream(body: ChatRequest) -> StreamingResponse:
    live = _want_live(body)

    async def gen_mock():
        for event in pick_demo(body.query):
            yield _sse(event)
            await asyncio.sleep(0.015)

    async def gen_live():
        yield _sse({"type": "status", "label": "Searching institute documents..."})
        try:
            result = await asyncio.to_thread(rag.answer, body.query)
        except Exception as err:  # noqa: BLE001
            yield _sse({"type": "token", "text": f"RAG error: {err}"})
            yield _sse({"type": "done"})
            return
        # stream token in slices; other events first
        for event in _events_from_result(result):
            if event.get("type") == "token":
                text = event["text"]
                step = 120
                for i in range(0, len(text), step):
                    yield _sse({"type": "token", "text": text[i : i + step]})
                    await asyncio.sleep(0.008)
            else:
                yield _sse(event)

    return StreamingResponse(
        gen_live() if live else gen_mock(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/sync", response_model=ChatSyncResponse)
async def chat_sync(body: ChatRequest) -> ChatSyncResponse:
    live = _want_live(body)
    if not live:
        text_parts = []
        sources = []
        structures = []
        freshness = None
        contradiction = None
        for event in pick_demo(body.query):
            if event["type"] == "token":
                text_parts.append(event["text"])
            elif event["type"] == "sources":
                sources = event["items"]
            elif event["type"] == "structure":
                structures.append(event)
            elif event["type"] == "freshness":
                freshness = {"asOf": event["asOf"], "lastUpdated": event["lastUpdated"]}
            elif event["type"] == "contradiction":
                contradiction = event
        return ChatSyncResponse(
            text="".join(text_parts),
            sources=sources,
            structures=structures,
            freshness=freshness,
            contradiction=contradiction,
            mode="mock",
        )
    result = await asyncio.to_thread(rag.answer, body.query)
    return ChatSyncResponse(
        text=result.get("text") or "",
        sources=result.get("sources") or [],
        structures=result.get("structures") or [],
        freshness=result.get("freshness"),
        contradiction=result.get("contradiction"),
        mode="live",
    )
