from __future__ import annotations

from pydantic import BaseModel, Field


class Source(BaseModel):
    n: int
    title: str
    url: str = ""
    page: int | None = None
    excerpt: str = ""
    effective_from: str | None = None
    last_updated: str | None = None
    document_id: str | None = None


class StructureCard(BaseModel):
    kind: str = "table"
    title: str
    rows: list[dict] = Field(default_factory=list)
    document_id: str | None = None
    page: int | None = None


class Contradiction(BaseModel):
    claim: str
    a: Source
    b: Source


class ChatRequest(BaseModel):
    query: str
    conversation_id: str | None = None
    as_of: str | None = None
    mock: bool | None = None


class ChatSyncResponse(BaseModel):
    text: str
    sources: list[Source] = Field(default_factory=list)
    structures: list[dict] = Field(default_factory=list)
    freshness: dict | None = None
    contradiction: dict | None = None
    mode: str = "live"
