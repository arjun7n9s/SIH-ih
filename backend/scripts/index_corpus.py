"""Build chunks.jsonl + embeddings.jsonl from downloaded corpus."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))
load_dotenv(REPO / ".env")

PDF_DIR = REPO / "data" / "corpus" / "pdfs"
HTML_DIR = REPO / "data" / "corpus" / "html"
MANIFEST = REPO / "data" / "corpus" / "manifest.yaml"
OUT_DIR = REPO / "data" / "index"
CHUNKS = OUT_DIR / "chunks.jsonl"
EMBEDS = OUT_DIR / "embeddings.jsonl"


def chunk_text(text: str, size: int = 1200, overlap: int = 150) -> list[str]:
    text = " ".join(text.split())
    if not text:
        return []
    out: list[str] = []
    i = 0
    while i < len(text):
        out.append(text[i : i + size])
        i += size - overlap
    return out


def _jsonable(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def manifest_meta() -> dict[str, dict]:
    if not MANIFEST.exists():
        return {}
    docs = yaml.safe_load(MANIFEST.read_text(encoding="utf-8")).get("documents", [])
    out: dict[str, dict] = {}
    for d in docs:
        out[d["id"]] = {k: _jsonable(v) for k, v in d.items()}
    return out


def main() -> int:
    try:
        import fitz
    except ImportError:
        print("pymupdf missing")
        return 1

    from app.services import aimlapi

    meta = manifest_meta()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []

    for pdf in sorted(PDF_DIR.glob("*.pdf")) if PDF_DIR.exists() else []:
        info = meta.get(pdf.stem, {})
        doc = fitz.open(pdf)
        for page_i, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            for part in chunk_text(text):
                rows.append(
                    {
                        "id": f"{pdf.stem}-p{page_i}-{len(rows)}",
                        "document_id": pdf.stem,
                        "title": info.get("title", pdf.stem),
                        "url": info.get("url", ""),
                        "page": page_i,
                        "text": part,
                        "effective_from": info.get("effective_from"),
                        "last_updated": info.get("last_updated"),
                        "source": str(pdf),
                    }
                )
        doc.close()

    for md in sorted(HTML_DIR.glob("*.md")) if HTML_DIR.exists() else []:
        info = meta.get(md.stem, {})
        text = md.read_text(encoding="utf-8")
        for part in chunk_text(text):
            rows.append(
                {
                    "id": f"{md.stem}-{len(rows)}",
                    "document_id": md.stem,
                    "title": info.get("title", md.stem),
                    "url": info.get("url", ""),
                    "page": None,
                    "text": part,
                    "effective_from": info.get("effective_from"),
                    "last_updated": info.get("last_updated"),
                    "source": str(md),
                }
            )

    with CHUNKS.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{len(rows)} chunks -> {CHUNKS}")

    if not rows:
        print("Run fetch_corpus first")
        return 1

    if aimlapi.client():
        print("Embedding via AIMLAPI...")
        batch = 32
        with EMBEDS.open("w", encoding="utf-8") as fh:
            for i in range(0, len(rows), batch):
                chunk = rows[i : i + batch]
                vectors = aimlapi.embed_texts([c["text"] for c in chunk])
                for c, emb in zip(chunk, vectors):
                    fh.write(
                        json.dumps({"id": c["id"], "embedding": emb}, ensure_ascii=False)
                        + "\n"
                    )
                print(f"  embedded {min(i + batch, len(rows))}/{len(rows)}")
        print(f"embeddings -> {EMBEDS}")
    else:
        print("No AIMLAPI_KEY - lexical retrieval only")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
