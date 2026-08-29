"""OCR scanned fee/refund PDFs via AIMLAPI vision and merge into the JSONL index."""

from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))
load_dotenv(REPO / ".env")

PDF_DIR = REPO / "data" / "corpus" / "pdfs"
CHUNKS = REPO / "data" / "index" / "chunks.jsonl"
EMBEDS = REPO / "data" / "index" / "embeddings.jsonl"
TABLES = REPO / "data" / "index" / "tables.json"

TARGETS = {
    "fee-ug-2024": {
        "title": "Fee structure B.Tech / B.Des 2024-25",
        "url": "https://www.iiitdmj.ac.in/academics/download/fee-structure-2024-25/UG2024.pdf",
        "effective_from": "2024-07-01",
        "last_updated": "2024-07-01",
        "prompt": (
            "This is the IIITDM Jabalpur UG B.Tech/B.Des fee structure PDF page. "
            "Extract every fee head and amount in clear plain text. "
            "Then output a JSON object with keys: "
            "plain_text (string, full readable extraction), "
            "tables (array of {title, rows} where rows are arrays of string cells). "
            "JSON only, no markdown."
        ),
    },
    "refund-2023": {
        "title": "Notification — Revised refund rule",
        "url": "https://www.iiitdmj.ac.in/downloads/Notification_Revised_refund_rule.pdf",
        "effective_from": "2023-05-15",
        "last_updated": "2023-05-15",
        "prompt": (
            "This is the IIITDM Jabalpur revised refund rule notification. "
            "Extract the refund slabs and rules as plain text. "
            "Output JSON: plain_text (string), tables (array of {title, rows}). "
            "JSON only, no markdown."
        ),
    },
}


def _page_pngs(pdf_path: Path) -> list[bytes]:
    import fitz

    doc = fitz.open(pdf_path)
    out: list[bytes] = []
    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)
        out.append(pix.tobytes("png"))
    doc.close()
    return out


def _vision_extract(png: bytes, prompt: str) -> dict:
    from app.services import aimlapi

    c = aimlapi.client()
    if not c:
        raise RuntimeError("AIMLAPI_KEY missing")
    b64 = base64.b64encode(png).decode("ascii")
    res = c.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}"},
                    },
                ],
            }
        ],
        temperature=0,
        max_tokens=2500,
    )
    raw = (res.choices[0].message.content or "").strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.I | re.M).strip()
    return json.loads(raw)


def _chunk_text(text: str, size: int = 1100, overlap: int = 120) -> list[str]:
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
    from app.services import aimlapi

    if not aimlapi.client():
        print("AIMLAPI_KEY missing")
        return 1

    new_chunks: list[dict] = []
    new_tables: list[dict] = []

    for doc_id, meta in TARGETS.items():
        pdf = PDF_DIR / f"{doc_id}.pdf"
        if not pdf.exists():
            print("missing", pdf)
            continue
        pages = _page_pngs(pdf)
        print(f"OCR {doc_id}: {len(pages)} page(s)")
        texts: list[str] = []
        for p_i, png in enumerate(pages, start=1):
            data = _vision_extract(png, meta["prompt"])
            plain = (data.get("plain_text") or "").strip()
            texts.append(plain)
            for t_i, table in enumerate(data.get("tables") or []):
                rows_raw = table.get("rows") or []
                if len(rows_raw) < 2:
                    continue
                header = [str(c or "").strip() or f"col{j}" for j, c in enumerate(rows_raw[0])]
                rows = []
                for raw in rows_raw[1:]:
                    if not raw:
                        continue
                    row = {
                        header[j] if j < len(header) else f"col{j}": str(raw[j] if j < len(raw) else "").strip()
                        for j in range(max(len(header), len(raw)))
                    }
                    if any(row.values()):
                        rows.append(row)
                if rows:
                    new_tables.append(
                        {
                            "id": f"{doc_id}-p{p_i}-t{t_i}",
                            "document_id": doc_id,
                            "page": p_i,
                            "kind": "table",
                            "title": table.get("title") or f"{meta['title']} (p.{p_i})",
                            "rows": rows[:40],
                        }
                    )
            print(f"  page {p_i}: {len(plain)} chars, tables so far {len(new_tables)}")

        full = "\n\n".join(t for t in texts if t)
        for part in _chunk_text(full):
            new_chunks.append(
                {
                    "id": f"{doc_id}-{len(new_chunks)}",
                    "document_id": doc_id,
                    "title": meta["title"],
                    "url": meta["url"],
                    "page": 1,
                    "text": part,
                    "effective_from": meta["effective_from"],
                    "last_updated": meta["last_updated"],
                    "source": str(pdf),
                }
            )

    if not new_chunks:
        print("no chunks produced")
        return 1

    # rewrite chunks: drop old fee-ug / refund rows, append new
    drop = set(TARGETS)
    kept: list[dict] = []
    if CHUNKS.exists():
        for line in CHUNKS.open(encoding="utf-8"):
            row = json.loads(line)
            if row.get("document_id") in drop:
                continue
            kept.append(row)
    kept.extend(new_chunks)
    with CHUNKS.open("w", encoding="utf-8") as fh:
        for row in kept:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"chunks -> {len(kept)} (added {len(new_chunks)})")

    # embeddings: keep non-dropped, embed new
    keep_ids = {r["id"] for r in kept}
    old_emb: dict[str, list[float]] = {}
    if EMBEDS.exists():
        for line in EMBEDS.open(encoding="utf-8"):
            row = json.loads(line)
            if row.get("id") in keep_ids:
                old_emb[row["id"]] = row["embedding"]
    need = [r for r in new_chunks if r["id"] not in old_emb]
    print(f"embedding {len(need)} new chunks…")
    batch = 16
    for i in range(0, len(need), batch):
        chunk = need[i : i + batch]
        vectors = aimlapi.embed_texts([c["text"] for c in chunk])
        for c, emb in zip(chunk, vectors):
            old_emb[c["id"]] = emb
        print(f"  {min(i + batch, len(need))}/{len(need)}")
    with EMBEDS.open("w", encoding="utf-8") as fh:
        for r in kept:
            emb = old_emb.get(r["id"])
            if emb is None:
                continue
            fh.write(json.dumps({"id": r["id"], "embedding": emb}, ensure_ascii=False) + "\n")

    tables = []
    if TABLES.exists():
        tables = [
            t
            for t in json.loads(TABLES.read_text(encoding="utf-8"))
            if t.get("document_id") not in drop
        ]
    tables.extend(new_tables)
    TABLES.write_text(json.dumps(tables, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"tables -> {len(tables)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
