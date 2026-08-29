"""Speechmatics: Realtime JWT + Melia-1 batch for multilingual / Hinglish.

Melia 1 (`melia-1`, language `multi`) is Batch-only today.
Realtime mic uses Enhanced until Melia RT ships; frontend should prefer
batch Melia when the user uploads a clip, and Enhanced RT for the live mic.
"""

from __future__ import annotations

import json
import time

import httpx

from app.config import settings

JWT_URL = "https://mp.speechmatics.com/v1/api_keys"
BATCH_URL = "https://eu1.asr.api.speechmatics.com/v2/jobs"


def _headers() -> dict[str, str]:
    if not settings.speechmatics_api_key:
        raise RuntimeError("SPEECHMATICS_API_KEY missing")
    return {
        "Authorization": f"Bearer {settings.speechmatics_api_key}",
    }


def mint_rt_jwt(ttl: int | None = None) -> dict:
    ttl = ttl or settings.speechmatics_jwt_ttl_seconds
    ttl = max(60, min(int(ttl), 3600))
    res = httpx.post(
        JWT_URL,
        params={"type": "rt"},
        headers={**_headers(), "Content-Type": "application/json"},
        json={"ttl": ttl},
        timeout=30,
    )
    if not res.is_success:
        raise RuntimeError(f"Speechmatics JWT failed HTTP {res.status_code}: {res.text[:200]}")
    body = res.json()
    token = body.get("key_value") or body.get("key") or body.get("token") or ""
    if not token:
        raise RuntimeError(f"Speechmatics JWT response missing key: {body}")
    return {
        "token": token,
        "ttl": ttl,
        "region_hint": "wss://global.rt.speechmatics.com/v2",
        "transcription_config": realtime_transcription_config(),
        "note": (
            "Melia-1 is Batch-only. Realtime uses Enhanced; for Hinglish/code-switch "
            "prefer POST /api/voice/batch with Melia, or Enhanced RT with hi/en."
        ),
    }


def realtime_transcription_config() -> dict:
    """Config for browser Realtime SDK StartRecognition message.

    Melia-1 is Batch-only. `language_hints` is a Melia field — do not send it
    on Enhanced/Standard or StartRecognition is rejected.
    There is no hi+en bilingual pack; live mic is single-language Enhanced.
    """
    return {
        "language": settings.speechmatics_realtime_language,
        "model": settings.speechmatics_realtime_model,
        "enable_partials": True,
        "max_delay": 1.5,
        "additional_vocab": [
            {"content": "IIITDMJ"},
            {"content": "IIITDM"},
            {"content": "PDPM"},
            {"content": "Jabalpur"},
            {"content": "JoSAA"},
            {"content": "CSAB"},
            {"content": "DUGC"},
            {"content": "ordinances"},
        ],
    }


def melia_batch_config() -> dict:
    """Official Melia-1 batch config: model=melia-1, language=multi.

    language_hints bias detection toward campus Hinglish without restricting
    other languages. additional_vocab is not supported on Melia yet.
    """
    hints = [h.strip() for h in settings.speechmatics_language_hints.split(",") if h.strip()]
    transcription: dict = {
        "model": settings.speechmatics_batch_model,
        "language": "multi",
    }
    if hints:
        transcription["language_hints"] = hints
    return {"type": "transcription", "transcription_config": transcription}


def voice_public_config() -> dict:
    return {
        "batch": {
            "model": settings.speechmatics_batch_model,
            "language": "multi",
            "endpoint": "POST /api/voice/batch",
            "multilingual": True,
            "config": melia_batch_config()["transcription_config"],
        },
        "realtime": {
            "model": settings.speechmatics_realtime_model,
            "language": settings.speechmatics_realtime_language,
            "multilingual": False,
            "jwt_endpoint": "GET /api/voice/jwt",
            "ws": "wss://global.rt.speechmatics.com/v2",
            "config": realtime_transcription_config(),
            "limitation": "Melia-1 realtime not available yet; use batch Melia for Hinglish clips.",
        },
    }


def transcribe_batch(filename: str, audio: bytes, timeout_s: float = 120.0) -> dict:
    """Multilingual Melia-1 batch transcription."""
    config = melia_batch_config()
    files = {
        "config": (None, json.dumps(config), "application/json"),
        "data_file": (filename or "audio.wav", audio, "application/octet-stream"),
    }
    res = httpx.post(BATCH_URL, headers=_headers(), files=files, timeout=60)
    if not res.is_success:
        raise RuntimeError(f"Speechmatics batch create failed HTTP {res.status_code}: {res.text[:300]}")
    job = res.json()
    job_id = job.get("id") or (job.get("job") or {}).get("id")
    if not job_id:
        raise RuntimeError(f"Speechmatics batch missing job id: {job}")

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        st = httpx.get(f"{BATCH_URL}/{job_id}", headers=_headers(), timeout=30)
        st.raise_for_status()
        body = st.json()
        status = (body.get("job") or body).get("status")
        if status == "done":
            tr = httpx.get(
                f"{BATCH_URL}/{job_id}/transcript",
                params={"format": "json-v2"},
                headers=_headers(),
                timeout=60,
            )
            tr.raise_for_status()
            data = tr.json()
            txt = httpx.get(
                f"{BATCH_URL}/{job_id}/transcript",
                params={"format": "txt"},
                headers=_headers(),
                timeout=60,
            )
            text = txt.text.strip() if txt.is_success else _plain_text(data)
            return {
                "job_id": job_id,
                "model": settings.speechmatics_batch_model,
                "text": text,
                "languages": _languages(data),
            }
        if status in {"rejected", "deleted", "expired"}:
            raise RuntimeError(f"Speechmatics job {job_id} status={status}")
        time.sleep(1.5)
    raise RuntimeError(f"Speechmatics job {job_id} timed out")


def _plain_text(data: dict) -> str:
    results = data.get("results") or []
    parts: list[str] = []
    for item in results:
        if item.get("type") != "word":
            continue
        alts = item.get("alternatives") or []
        if alts:
            parts.append(alts[0].get("content", ""))
    # Speechmatics often puts spaces as separate tokens; join carefully
    out = []
    for p in parts:
        if p in {".", ",", "!", "?", ";", ":"} and out:
            out[-1] = out[-1] + p
        else:
            out.append(p)
    return " ".join(out).strip()


def _languages(data: dict) -> list[str]:
    langs = set()
    for item in data.get("results") or []:
        for alt in item.get("alternatives") or []:
            lang = alt.get("language")
            if lang:
                langs.add(lang)
    meta = data.get("metadata") or {}
    for lang in meta.get("language_codes") or meta.get("languages") or []:
        langs.add(lang)
    return sorted(langs)
