"""
Suchna — college knowledge assistant for PDPM IIITDM Jabalpur.

Hackathon track 2. UI first, then RAG. See PLANNING.md.

## Quick start

```bash
cp .env.example .env   # paste keys; leave USE_MOCK=1 until the index exists

# backend
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -e .
uvicorn app.main:app --reload --app-dir .

# frontend (another terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — empty-state chips play the 4-minute demo against mock SSE.

## Corpus

Do not use Tingle Scraper Studio collectors (`TINGLE_C_*`). Those are CSS extractors that break.

Fetch uses:
1. `curl_cffi` Chrome impersonation (free)
2. Bright Data **Web Unlocker** (`POST https://api.brightdata.com/request`) when the institute WAF 403s

```bash
cd backend
python -m scripts.fetch_corpus --demo-only
python -m scripts.fetch_corpus --demo-only --discover
python -m scripts.index_corpus
```

Fill `BRIGHT_DATA_API_TOKEN` and `BRIGHT_DATA_UNLOCKER_ZONE` in `.env` (same Unlocker zone as Tingle, not the Studio `c_*` ids).
"""
