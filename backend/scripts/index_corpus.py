"""Parse downloaded PDFs/HTML into chunks.jsonl. Chroma is Block B.

Usage (from backend/):
  python -m scripts.index_corpus
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))
load_dotenv(REPO / ".env")

PDF_DIR = REPO / "data" / "corpus" / "pdfs"
HTML_DIR = REPO / "data" / "corpus" / "html"
OUT = REPO / "data" / "index" / "chunks.jsonl"


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


def main() -> int:
    try:
        import fitz  # pymupdf
    except ImportError:
        print("pip install pymupdf pdfplumber  (from backend/)")
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []

    for pdf in sorted(PDF_DIR.glob("*.pdf")) if PDF_DIR.exists() else []:
        doc = fitz.open(pdf)
        for page_i, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            for part in chunk_text(text):
                rows.append(
                    {
                        "id": f"{pdf.stem}-p{page_i}-{len(rows)}",
                        "document_id": pdf.stem,
                        "page": page_i,
                        "text": part,
                        "source": str(pdf),
                    }
                )
        doc.close()

    for md in sorted(HTML_DIR.glob("*.md")) if HTML_DIR.exists() else []:
        text = md.read_text(encoding="utf-8")
        for part in chunk_text(text):
            rows.append(
                {
                    "id": f"{md.stem}-{len(rows)}",
                    "document_id": md.stem,
                    "page": None,
                    "text": part,
                    "source": str(md),
                }
            )

    with OUT.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"{len(rows)} chunks → {OUT}")
    if len(rows) < 1:
        print("Run: python -m scripts.fetch_corpus --demo-only")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
