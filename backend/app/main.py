from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Monorepo .env (local). On Vercel, platform env vars are injected — no file needed.
_here = Path(__file__).resolve()
load_dotenv(_here.parents[2] / ".env")  # SIHih/.env
load_dotenv(_here.parents[1] / ".env")  # backend/.env

from app.config import settings  # noqa: E402
from app.routers import chat, companion, contradictions, corpus, voice  # noqa: E402
from app.services import rag, store  # noqa: E402

app = FastAPI(
    title="Suchna API",
    version="0.2.0",
    description="IIITDM Jabalpur knowledge assistant backend. SSE chat + contradictions + companion + voice JWT.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(contradictions.router)
app.include_router(companion.router)
app.include_router(voice.router)
app.include_router(corpus.router)


@app.get("/health")
def health() -> dict:
    stats = store.index_stats()
    return {
        "ok": True,
        "service": "suchna-api",
        "version": "0.2.0",
        "mock": settings.use_mock,
        "live_chat": (not settings.use_mock) and bool(settings.aimlapi_key) and stats["ready"],
        "aimlapi": bool(settings.aimlapi_key),
        "unlocker": bool(settings.bd_token and settings.bright_data_unlocker_zone),
        "speechmatics": bool(settings.speechmatics_api_key),
        "index": stats,
    }


@app.get("/api/ready")
def ready() -> dict:
    stats = store.index_stats()
    return {
        "ready": stats["ready"] and bool(settings.aimlapi_key),
        "index": stats,
        "mode": "live" if ((not settings.use_mock) and stats["ready"] and settings.aimlapi_key) else "mock",
    }
