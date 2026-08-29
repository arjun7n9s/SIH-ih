from fastapi import APIRouter, HTTPException

from app.config import settings

router = APIRouter(prefix="/api", tags=["voice"])


@router.get("/voice/jwt")
async def voice_jwt() -> dict:
    if not settings.speechmatics_api_key:
        raise HTTPException(
            status_code=501,
            detail="SPEECHMATICS_API_KEY not set. Mic uses the official Speechmatics React SDK; this route only mints a JWT.",
        )
    # Real JWT mint is Block E. Placeholder so the frontend has a contract.
    return {
        "token": "",
        "ttl": settings.speechmatics_jwt_ttl_seconds,
        "note": "Wire Speechmatics management API here. Do not put the long-lived key in the browser.",
    }
