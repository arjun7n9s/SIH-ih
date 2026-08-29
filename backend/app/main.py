from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Repo-root .env (parent of backend/)
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from app.config import settings  # noqa: E402
from app.routers import chat, companion, contradictions, voice  # noqa: E402

app = FastAPI(title="Suchna", version="0.1.0")
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


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "mock": settings.use_mock,
        "aimlapi": bool(settings.aimlapi_key),
        "unlocker": bool(settings.bd_token and settings.bright_data_unlocker_zone),
        "speechmatics": bool(settings.speechmatics_api_key),
    }
