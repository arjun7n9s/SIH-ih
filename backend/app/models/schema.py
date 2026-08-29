from __future__ import annotations

from pydantic import BaseModel, Field


class Source(BaseModel):
    n: int
    title: str
    url: str
    page: int | None = None
    excerpt: str = ""
    effective_from: str | None = None
    last_updated: str | None = None


class StructureCard(BaseModel):
    kind: str
    title: str
    rows: list[dict] = Field(default_factory=list)


class Contradiction(BaseModel):
    claim: str
    a: Source
    b: Source


class ChatRequest(BaseModel):
    query: str
    conversation_id: str | None = None
