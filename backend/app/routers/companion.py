from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services import companion as companion_svc

router = APIRouter(prefix="/api", tags=["companion"])


@router.post("/companion")
async def companion_upload(file: UploadFile = File(...)) -> dict:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="empty file")
    if len(data) > 12_000_000:
        raise HTTPException(status_code=413, detail="max 12MB")
    return companion_svc.create_session(file.filename or "upload.bin", data)


@router.get("/companion/{session_id}")
async def companion_get(session_id: str) -> dict:
    row = companion_svc.get_session(session_id)
    if not row:
        raise HTTPException(status_code=404, detail="session expired or missing")
    return row
