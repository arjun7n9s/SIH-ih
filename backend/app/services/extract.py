"""Structured table extraction from fee/refund PDFs via pdfplumber."""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PDF_DIR = REPO / "data" / "corpus" / "pdfs"
OUT = REPO / "data" / "index" / "tables.json"

# Prefer these ids for StructuredCard demos
TARGET_IDS = ("fee-ug-2024", "fee-phd-2025", "refund-2023")


def extract_pdf_tables(pdf_path: Path, doc_id: str) -> list[dict]:
    import pdfplumber

    cards: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables() or []
            for t_i, table in enumerate(tables):
                if not table or len(table) < 2:
                    continue
                header = [str(c or "").strip() or f"col{j}" for j, c in enumerate(table[0])]
                rows = []
                for raw in table[1:]:
                    if not raw or not any(raw):
                        continue
                    row = {
                        header[j] if j < len(header) else f"col{j}": str(raw[j] or "").strip()
                        for j in range(len(raw))
                    }
                    if any(row.values()):
                        rows.append(row)
                if not rows:
                    continue
                cards.append(
                    {
                        "id": f"{doc_id}-p{i}-t{t_i}",
                        "document_id": doc_id,
                        "page": i,
                        "kind": "table",
                        "title": f"{doc_id} table (p.{i})",
                        "rows": rows[:40],
                    }
                )
    return cards


def build_tables(doc_ids: tuple[str, ...] = TARGET_IDS) -> list[dict]:
    all_cards: list[dict] = []
    for doc_id in doc_ids:
        path = PDF_DIR / f"{doc_id}.pdf"
        if not path.exists():
            continue
        all_cards.extend(extract_pdf_tables(path, doc_id))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(all_cards, ensure_ascii=False, indent=2), encoding="utf-8")
    return all_cards


def tables_for_docs(doc_ids: list[str], limit: int = 2) -> list[dict]:
    from app.services import store

    wanted = set(doc_ids)
    hits = [t for t in store.tables() if t.get("document_id") in wanted]
    return hits[:limit]
