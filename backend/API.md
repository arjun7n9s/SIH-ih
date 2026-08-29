# Suchna Backend — frontend integration contract

Base URL (local): `http://127.0.0.1:8000`  
OpenAPI: `http://127.0.0.1:8000/docs`

## Run

```bash
cd backend
.\.venv\Scripts\activate   # or: source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Env lives in repo-root `.env` (`USE_MOCK=0` for live RAG).

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Keys + index stats |
| GET | `/api/ready` | `{ ready, mode: live\|mock }` |
| POST | `/api/chat` | **SSE** streaming answer (primary) |
| POST | `/api/chat/sync` | JSON one-shot answer |
| GET | `/api/contradictions` | Seeded disagreement cards |
| GET | `/api/documents` | Corpus manifest |
| GET | `/api/extract` | Extracted fee/refund tables |
| POST | `/api/companion` | `multipart/form-data` file upload (ephemeral) |
| GET | `/api/companion/{id}` | Fetch companion session |
| GET | `/api/voice/config` | Melia batch vs Enhanced realtime config for the frontend SDK |
| GET | `/api/voice/jwt` | Speechmatics Realtime temp JWT + Enhanced StartRecognition config |
| POST | `/api/voice/batch` | Melia-1 multilingual transcription (`multipart` field `file`) |

## SSE event types (`POST /api/chat`)

```
data: {"type":"status","label":"..."}
data: {"type":"freshness","asOf":"2025-12-01","lastUpdated":"2025-12-01"}
data: {"type":"sources","items":[Source,...]}
data: {"type":"structure","kind":"table","title":"...","rows":[...]}
data: {"type":"token","text":"..."}          # may repeat
data: {"type":"contradiction","claim":"...","a":Source,"b":Source}
data: {"type":"done"}
```

### Source

```ts
type Source = {
  n: number
  title: string
  url: string
  page: number | null
  excerpt: string
  effective_from?: string | null
  last_updated?: string | null
  document_id?: string | null
}
```

### Chat body

```json
{ "query": "What is the hostel fee?", "mock": false }
```

`mock: true` forces fixture demo. Omit / `false` uses live index when ready.

## Voice

Melia-1 (`model: "melia-1"`, `language: "multi"`) is the multilingual / Hinglish model. It is **Batch-only** today (EU/US). Live mic uses Enhanced until Speechmatics ships Melia realtime. There is no `hi_en` bilingual pack.

**Hinglish / code-switch clip (correct Melia path)**

1. `POST /api/voice/batch` with `file` = audio blob
2. Response: `{ job_id, model: "melia-1", text, languages }`

**Live mic (Enhanced until Melia RT exists)**

1. `GET /api/voice/config` for the StartRecognition payload
2. `GET /api/voice/jwt` → `{ token, ttl, region_hint, transcription_config }`
3. Browser `@speechmatics/real-time-client-react` connects with that JWT (never the long-lived key)

Do **not** send `language_hints` on Enhanced realtime — that field is Melia-only and will fail `StartRecognition`.

## Companion

`POST /api/companion` with field name `file`. Response is not persisted server-side beyond ~10 minutes.

## CORS

Default allows localhost `5173`, `5174`, `3000`. Override with `CORS_ORIGINS` comma-list.
