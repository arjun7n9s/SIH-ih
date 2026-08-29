"""OpenAI-compatible AIMLAPI client."""

from __future__ import annotations

from openai import OpenAI

from app.config import settings


def client() -> OpenAI | None:
    if not settings.aimlapi_key:
        return None
    return OpenAI(api_key=settings.aimlapi_key, base_url=settings.aimlapi_base_url)


def embed_texts(texts: list[str]) -> list[list[float]]:
    c = client()
    if not c or not texts:
        return []
    res = c.embeddings.create(model=settings.aimlapi_embed_model, input=texts)
    return [row.embedding for row in res.data]


def chat_completion(system: str, user: str) -> str:
    c = client()
    if not c:
        raise RuntimeError("AIMLAPI_KEY missing")
    res = c.chat.completions.create(
        model=settings.aimlapi_chat_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    return (res.choices[0].message.content or "").strip()
