"""Ephemeral classroom companion — in-memory, auto-expires."""

from __future__ import annotations

import time
import uuid

from app.services import aimlapi

TTL_SECONDS = 600
_SESSIONS: dict[str, dict] = {}


def _purge() -> None:
    now = time.time()
    dead = [k for k, v in _SESSIONS.items() if v["expires_at"] < now]
    for k in dead:
        _SESSIONS.pop(k, None)


def _pdf_text(data: bytes) -> str:
    try:
        import fitz

        doc = fitz.open(stream=data, filetype="pdf")
        parts = [(page.get_text("text") or "") for page in doc]
        doc.close()
        return "\n".join(parts)
    except Exception:  # noqa: BLE001
        return ""


def create_session(filename: str, data: bytes) -> dict:
    _purge()
    text = ""
    if filename.lower().endswith(".pdf") or data[:5] == b"%PDF-":
        text = _pdf_text(data)
    if not text:
        try:
            text = data.decode("utf-8", errors="ignore")
        except Exception:  # noqa: BLE001
            text = ""
    text = text[:12000]

    summary = "Could not read this upload."
    due: list[str] = []
    open_questions: list[str] = []
    key_points: list[str] = []

    if text and aimlapi.client():
        import json
        import re

        raw = aimlapi.chat_completion(
            "Summarize a class handout for a student. JSON only.",
            (
                "Return JSON with keys summary (string), due (string[]), "
                "open_questions (string[]), key_points (string[]).\n\n"
                f"Handout:\n{text}"
            ),
        )
        try:
            m = re.search(r"\{.*\}", raw, re.S)
            data_j = json.loads(m.group(0)) if m else {}
            summary = data_j.get("summary") or raw[:500]
            due = data_j.get("due") or []
            open_questions = data_j.get("open_questions") or []
            key_points = data_j.get("key_points") or []
        except Exception:  # noqa: BLE001
            summary = raw[:800]
    elif text:
        summary = text[:500]

    sid = uuid.uuid4().hex
    payload = {
        "id": sid,
        "saved": False,
        "banner": "This session is not saved. It expires in 10 minutes or on refresh.",
        "filename": filename,
        "bytes": len(data),
        "summary": summary,
        "due": due,
        "open_questions": open_questions,
        "key_points": key_points,
        "expires_at": time.time() + TTL_SECONDS,
    }
    _SESSIONS[sid] = payload
    return {k: v for k, v in payload.items() if k != "expires_at"} | {
        "expires_in": TTL_SECONDS
    }


def get_session(session_id: str) -> dict | None:
    _purge()
    row = _SESSIONS.get(session_id)
    if not row:
        return None
    return {k: v for k, v in row.items() if k != "expires_at"}
