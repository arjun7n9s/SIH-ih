from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.services import speechmatics

router = APIRouter(prefix="/api", tags=["voice"])


@router.get("/voice/jwt")
async def voice_jwt(ttl: int | None = Query(default=None, ge=60, le=3600)) -> dict:
    if not settings.speechmatics_api_key:
        raise HTTPException(
            status_code=501,
            detail="SPEECHMATICS_API_KEY not set",
        )
    try:
        return speechmatics.mint_rt_jwt(ttl)
    except Exception as err:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(err)) from err
