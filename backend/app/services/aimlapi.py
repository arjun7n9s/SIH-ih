"""OpenAI-compatible AIMLAPI client."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

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


def chat_completion(
    system: str,
    user: str,
    *,
    temperature: float = 0.25,
    max_tokens: int = 700,
    model: str | None = None,
) -> str:
    c = client()
    if not c:
        raise RuntimeError("AIMLAPI_KEY missing")
    res = c.chat.completions.create(
        model=model or settings.aimlapi_chat_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    choice = res.choices[0].message if res.choices else None
    content = (choice.content if choice else None) or ""
    return content.strip()


def chat_completion_safe(
    system: str,
    user: str,
    *,
    temperature: float = 0.25,
    max_tokens: int = 700,
    model: str | None = None,
) -> str:
    try:
        return chat_completion(
            system,
            user,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
        )
    except Exception:  # noqa: BLE001
        return ""


def complete_parallel(
    jobs: list[dict],
) -> list[str]:
    """Run several chat completions at once. Each job: system, user, model, temperature, max_tokens."""
    if not jobs:
        return []

    def run(job: dict) -> tuple[int, str]:
        idx = int(job["i"])
        text = chat_completion_safe(
            job["system"],
            job["user"],
            temperature=float(job.get("temperature") or 0.25),
            max_tokens=int(job.get("max_tokens") or 520),
            model=job.get("model"),
        )
        return idx, text

    out = [""] * len(jobs)
    tagged = [{**job, "i": i} for i, job in enumerate(jobs)]
    with ThreadPoolExecutor(max_workers=min(4, len(jobs))) as pool:
        futs = [pool.submit(run, job) for job in tagged]
        for fut in as_completed(futs):
            idx, text = fut.result()
            out[idx] = text
    return out
