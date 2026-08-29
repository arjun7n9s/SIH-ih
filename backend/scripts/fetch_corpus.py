"""Download the IIITDMJ corpus.

Not Tingle Scraper Studio. Layered fetch:
  1. curl_cffi Chrome impersonation (free)
  2. Bright Data Web Unlocker if the WAF 403s

Usage (from backend/):
  python -m scripts.fetch_corpus
  python -m scripts.fetch_corpus --demo-only
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import yaml
from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))
load_dotenv(REPO / ".env")

from app.services.fetch import FetchError, fetch_bytes, fetch_text  # noqa: E402

MANIFEST = REPO / "data" / "corpus" / "manifest.yaml"
PDF_DIR = REPO / "data" / "corpus" / "pdfs"
HTML_DIR = REPO / "data" / "corpus" / "html"
HOST_OK = "iiitdmj.ac.in"
SKIP_SUBSTRINGS = (
    "allotment",
    "advertisement",
    "telephone",
    "taxi",
    "recruitment",
    "holiday",
)
PDF_RE = re.compile(r"https?://[^\s)\"']+\.pdf[^\s)\"']*", re.I)
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.I)


def load_manifest() -> dict:
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))


def allowed(url: str) -> bool:
    host = urlparse(url).hostname or ""
    if HOST_OK not in host:
        return False
    lower = url.lower()
    return not any(s in lower for s in SKIP_SUBSTRINGS)


def save_pdf(doc_id: str, url: str, content: bytes) -> Path:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    path = PDF_DIR / f"{doc_id}.pdf"
    path.write_bytes(content)
    return path


def save_html(doc_id: str, url: str, text: str) -> Path:
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    path = HTML_DIR / f"{doc_id}.md"
    path.write_text(f"<!-- source: {url} -->\n\n{text}", encoding="utf-8")
    return path


def fetch_document(doc: dict) -> dict:
    url = doc["url"]
    doc_id = doc["id"]
    path_l = urlparse(url).path.lower()
    is_html = doc.get("type") == "html" or path_l.endswith((".php", ".html", ".htm", "/"))
    if is_html and not path_l.endswith(".pdf"):
        text, via = fetch_text(url)
        path = save_html(doc_id, url, text)
        return {"id": doc_id, "via": via, "path": str(path), "kind": "html", "bytes": len(text.encode())}

    body, via = fetch_bytes(url, want_pdf=True)
    if body[:5] == b"%PDF-" or b"%PDF-" in body[:2048]:
        path = save_pdf(doc_id, url, body)
        return {"id": doc_id, "via": via, "path": str(path), "kind": "pdf", "bytes": len(body)}
    text = body.decode("utf-8", errors="replace")
    path = save_html(doc_id, url, text)
    return {"id": doc_id, "via": via, "path": str(path), "kind": "html", "bytes": len(body)}


def extract_links(text: str, base: str) -> list[str]:
    found: list[str] = []
    for match in PDF_RE.findall(text):
        found.append(match.split('"')[0].split(")")[0])
    for _, href in MD_LINK_RE.findall(text):
        found.append(urljoin(base, href.strip()))
    for href in HREF_RE.findall(text):
        found.append(urljoin(base, href.strip()))
    out: list[str] = []
    seen: set[str] = set()
    for raw in found:
        url = raw.split("#")[0].replace(" ", "%20")
        if url in seen or not allowed(url):
            continue
        seen.add(url)
        out.append(url)
    return out


def crawl_extra(seed_text: str, seed_url: str, existing: set[str], limit: int = 12) -> list[dict]:
    extra: list[dict] = []
    for url in extract_links(seed_text, seed_url):
        if url in existing:
            continue
        if not url.lower().split("?")[0].endswith(".pdf"):
            continue
        slug = Path(urlparse(url).path).stem[:40] or "extra"
        doc_id = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-") or "extra"
        if doc_id in existing:
            continue
        try:
            body, via = fetch_bytes(url, want_pdf=True)
        except (FetchError, OSError) as err:
            extra.append({"id": doc_id, "url": url, "error": str(err)})
            continue
        if not (body[:5] == b"%PDF-" or b"%PDF-" in body[:2048]):
            continue
        path = save_pdf(doc_id, url, body)
        existing.add(url)
        extra.append(
            {
                "id": doc_id,
                "url": url,
                "via": via,
                "path": str(path),
                "kind": "pdf",
                "bytes": len(body),
                "discovered": True,
            }
        )
        if len(extra) >= limit:
            break
    return extra


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo-only", action="store_true")
    parser.add_argument("--discover", action="store_true", help="Also grab extra PDFs linked from HTML pages")
    args = parser.parse_args()

    manifest = load_manifest()
    docs = manifest["documents"]
    if args.demo_only:
        docs = [d for d in docs if d.get("demo")]

    log: list[dict] = []
    seen_urls = {d["url"] for d in docs}

    for doc in docs:
        print(f"-> {doc['id']}  {doc['url']}")
        try:
            result = fetch_document(doc)
            print(f"  {result['kind']} via {result['via']}  {result['bytes']} bytes")
            log.append({**result, "url": doc["url"], "ok": True})
            if args.discover and result["kind"] == "html":
                text = Path(result["path"]).read_text(encoding="utf-8")
                found = crawl_extra(text, doc["url"], seen_urls)
                for item in found:
                    print(f"  discovered {item.get('id')} via {item.get('via', 'err')}")
                    log.append({**item, "ok": "error" not in item})
        except Exception as err:  # noqa: BLE001
            print(f"  FAIL {err}")
            log.append({"id": doc["id"], "url": doc["url"], "ok": False, "error": str(err)})

    report = REPO / "data" / "corpus" / "fetch_log.json"
    report.write_text(json.dumps(log, indent=2), encoding="utf-8")
    ok = sum(1 for row in log if row.get("ok"))
    print(f"\n{ok}/{len(log)} saved. log -> {report}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
