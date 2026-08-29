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

Backend contract for any frontend (including `front-end/`): see [`backend/API.md`](backend/API.md) and live docs at http://127.0.0.1:8000/docs

```bash
# API only
cd backend && .\.venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
curl http://127.0.0.1:8000/health
```

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
