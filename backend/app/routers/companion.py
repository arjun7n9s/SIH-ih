from fastapi import APIRouter, File, UploadFile

router = APIRouter(prefix="/api", tags=["companion"])

_SESSIONS: dict[str, dict] = {}


@router.post("/companion")
async def companion(file: UploadFile = File(...)) -> dict:
    data = await file.read()
    return {
        "saved": False,
        "banner": "This session is not saved. Refresh and it is gone.",
        "filename": file.filename,
        "bytes": len(data),
        "summary": "Companion summariser wires to AIMLAPI in Block F. Upload received.",
        "due": [],
        "open_questions": [],
    }
