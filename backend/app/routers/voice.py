from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.config import settings
from app.services import speechmatics

router = APIRouter(prefix="/api", tags=["voice"])


@router.get("/voice/config")
async def voice_config() -> dict:
    """Frontend: Melia batch vs Enhanced realtime config."""
    return speechmatics.voice_public_config()


@router.get("/voice/jwt")
async def voice_jwt(ttl: int | None = Query(default=None, ge=60, le=3600)) -> dict:
    if not settings.speechmatics_api_key:
        raise HTTPException(status_code=501, detail="SPEECHMATICS_API_KEY not set")
    try:
        return speechmatics.mint_rt_jwt(ttl)
    except Exception as err:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(err)) from err


@router.post("/voice/batch")
async def voice_batch(file: UploadFile = File(...)) -> dict:
    """Multilingual Melia-1 transcription (Hinglish / code-switch)."""
    if not settings.speechmatics_api_key:
        raise HTTPException(status_code=501, detail="SPEECHMATICS_API_KEY not set")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="empty audio")
    if len(data) > 25_000_000:
        raise HTTPException(status_code=413, detail="max 25MB")
    try:
        return speechmatics.transcribe_batch(file.filename or "audio.wav", data)
    except Exception as err:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(err)) from err
