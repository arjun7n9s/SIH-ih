# Suchna — Planning Document

> Multilingual, contradiction-aware knowledge assistant for **IIITDM Jabalpur**.
> Hackathon build: 1–2 days, Render + Speechmatics + AIMLAPI.

---

## 1. Problem statement (track 2)

> Build a retrieval-based question-answering system that responds to student queries using a defined set of college or institutional documents and provides relevant source references.

Every college chatbot on GitHub does the shallow version: drop PDFs into a vector store, ask a question, return text with `[1]` next to it. They fail in five ways we explicitly want to fix:

1. **Citations are decorative**, not actionable (no chunk preview, no page jump, no freshness).
2. **Multilingual India is ignored.** Students ask in Hindi or Hinglish; documents are in English. Vector spaces don't bridge them.
3. **Tables, dates, fee structures are lost.** RAG flattens them into prose; the actual answer is the table.
4. **No contradiction surfacing.** If the 2022 and 2024 refund policies disagree, the bot silently picks one.
5. **No recency signal.** A student asking about exam eligibility in October 2026 doesn't know the answer is from a 2023 PDF.

Suchna addresses all five, anchored to a real institution.

---

## 2. Target institution

**Indian Institute of Information Technology, Design and Manufacturing, Jabalpur** (PDPM IIITDM Jabalpur, est. 2009). Public institute under IIIT Act, MHRD.[19]

Why this college:
- Publishes a real corpus of downloadable PDFs (ordinances, academic guidelines, refund rules, scholarship notices, timetable, IPR policy, statutes gazette, hostel's banking/fee info).
- Indian technical institution = the demographic where a Hindi/Hinglish-aware assistant is genuinely needed.
- Documents overlap and occasionally contradict (e.g., refund rule 2017 vs 2024 revision), so the contradiction detector has real signal to find.

Initial corpus (8–10 documents fetched from `https://www.iiitdmj.ac.in`):
1. `Ordinances of PDPM-IIITDM Jabalpur.pdf`
2. `Annexure II – Academic Guidelines UG (modified Dec 2025).pdf`
3. `Ph.D. Manual.pdf`
4. `Guidelines for Timetable.pdf`
5. `Notification Revised refund rule.pdf`
6. `Activity Calendar of IIC 2.0 Innovation Cell.pdf`
7. `IIIT Act 30 of 2014.pdf`
8. `Statutes of IIITDM Jabalpur (Gazette).pdf`
9. `IPR Policy Final V1.pdf`
10. `Letter to Institutes for NSP 2.0.pdf`

---

## 3. Product name

**Suchna** — Hindi for "information, the act of finding out." 4 letters, hard consonant (S + ch + n), English-leaning, maps to the act rather than the description, fits naming taste.[user-profile]

---

## 4. Locked feature set

| # | Feature | Description | Phase |
|---|---|---|---|
| 1 | **Anomaly / Contradiction Detector** | At index time, cross-document comparison surfaces pairs that disagree on a shared numeric or policy claim. Surfaces as a side-by-side comparison card in chat results and a dedicated `/contradictions` page. | Phase 5 |
| 2 | **Multilingual RAG (Hindi/English/Hinglish)** | One multilingual embedding space (`intfloat/multilingual-e5-large`) lets Hindi queries retrieve English-only PDF chunks and vice versa. Replies in the user's language. | Phase 1–2 |
| 3 | **Structured Extraction Panel** | Tables, fee rows, deadlines, eligibility rules are parsed into typed rows and rendered as cards inside chat answers. Source chunk remains linkable. | Phase 4 |
| 4 | **Time-Aware Answers** | Every document row carries `last_updated` and `effective_from`. The answer renders a freshness badge and can answer "What was the rule in 2023?" by filtering on `effective_from`. | Phase 6 |
| 5 | **Live-Classroom Companion** (ephemeral, no persistence) | A single-session upload of a class handout (PDF or image). AI summarises, extracts "what's due," lists open questions. Nothing persists past the session, per user direction. | Phase 7 |
| 6 | **Voice Input (Hinglish)** | Mic button → Speechmatics Enhanced Realtime → text query → same RAG pipeline. Reply stays text for now. | Phase 8 |

### Out of scope (saved for "future scalable plan")

- Admin panel for document upload, version, expiry (you asked to defer this).
- Persistent user accounts and chat history.
- Multi-tenant (other colleges).
- TTS reply (Speechmatics TTS exists but adds latency we don't need for the demo).[5]

---

## 5. Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│ Browser                                                          │
│   React + Vite + Tailwind + shadcn/ui                            │
│   Free Render Static Site                                        │
└──────────────────────────────────────────────────────────────────┘
                          │ HTTPS
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│ Render Web Service  (FastAPI, Python 3.12)                       │
│   /api/chat           streaming RAG, Server-Sent Events         │
│   /api/voice          multipart audio → Speechmatics → RAG       │
│   /api/contradictions precomputed cross-doc conflicts            │
│   /api/extract        table/date/fee extraction results          │
│   /api/companion      ephemeral session for handout upload       │
└──────────────────────────────────────────────────────────────────┘
          │                                 │
          ▼                                 ▼
┌──────────────────────┐         ┌──────────────────────────────────┐
│ AIMLAPI              │         │ Speechmatics Enhanced Realtime   │
│  - chat completions  │         │  - Hindi + English + Hinglish    │
│  - embeddings (alt)  │         │  - $0.43/audio hour              │
└──────────────────────┘         └──────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────────┐
│ Postgres (Render)                                                │
│  documents(id, title, url, last_updated, effective_from, type)  │
│  chunks(id, document_id, page, text, embedding vector, lang)    │
│  contradictions(id, doc_a, doc_b, claim, value_a, value_b)      │
│  extracted_structures(id, doc_id, kind, payload jsonb)          │
└──────────────────────────────────────────────────────────────────┘
```

Local development uses SQLite + a `pgvector` shim or a separate vector cache so we can iterate without paying for Postgres during dev.

---

## 6. Stack — final picks and why

| Layer | Pick | Reason |
|---|---|---|
| Frontend | React + Vite + Tailwind + shadcn/ui | Best UI quality per byte of code; shadcn ships Perplexity-style chat primitives out of the box.[13] |
| Backend | FastAPI (Python 3.12) | Streaming via SSE is one line; Pydantic + async = good fit for RAG fan-out |
| Embeddings (prod) | `intfloat/multilingual-e5-large` via HuggingFace `text-embeddings-inference` (TEI) on Render | Single vector space for 100+ languages including Hindi; "Best for retrieval" benchmark performance on MTEB.[20][18] |
| Embeddings (alt) | AIMLAPI `text-embedding-3-small` | Lower quality for Hindi; use as fallback only |
| Generation | AIMLAPI `gpt-4o-mini` or `gpt-5-mini` (whichever has the best Hindi/JSON-mode combo at the moment) | Cheap, JSON-mode reliable, decent Hindi |
| STT | Speechmatics **Enhanced Realtime** (Batch Standard fallback)[1][2][6] | Speechmatics Enhanced is the highest-accuracy model and supports diarization + language ID; Realtime partials give us <500 ms first-token latency.[1][2] |
| Vector store | Postgres + `pgvector` extension (Render Postgres supports it from v15+)[11] | No extra service, single backup story, plays well with Render Blueprint[10] |
| Deployment | Render Blueprint via `render.yaml` | One-click deploy; matches our $500-credit plan[7][8][9] |
| Auth | None for demo; rate-limit by IP | Saves days of work |

---

## 7. Repository layout

```
C:\Users\arjun\Desktop\SIHih\
├── PLANNING.md                  ← this file
├── README.md                    ← public-facing, will appear in repo
├── render.yaml                  ← Render Blueprint
├── .gitignore
├── .env.example
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py              ← FastAPI app
│   │   ├── config.py
│   │   ├── deps.py
│   │   ├── routers/
│   │   │   ├── chat.py
│   │   │   ├── voice.py
│   │   │   ├── contradictions.py
│   │   │   ├── extract.py
│   │   │   └── companion.py
│   │   ├── services/
│   │   │   ├── rag.py
│   │   │   ├── embedding.py
│   │   │   ├── speechmatics_client.py
│   │   │   ├── aimlapi_client.py
│   │   │   ├── extractor.py
│   │   │   └── contradiction.py
│   │   ├── models/
│   │   │   └── schema.py        ← Pydantic types
│   │   └── prompts/
│   │       ├── chat_system.md
│   │       ├── extract_tables.md
│   │       └── contradiction_check.md
│   └── scripts/
│       ├── fetch_corpus.py      ← download 10 PDFs from iiitdmj.ac.in
│       ├── index_corpus.py      ← parse, chunk, embed, store
│       ├── build_contradictions.py
│       └── extract_structures.py
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── components/
│       │   ├── ChatPane.tsx
│       │   ├── MessageBubble.tsx
│       │   ├── SourcePanel.tsx
│       │   ├── ContradictionCard.tsx
│       │   ├── StructuredCard.tsx
│       │   ├── FreshnessBadge.tsx
│       │   ├── VoiceButton.tsx
│       │   └── CompanionUpload.tsx
│       ├── pages/
│       │   ├── Home.tsx
│       │   └── Contradictions.tsx
│       └── lib/
│           ├── api.ts
│           └── types.ts
├── data/
│   └── corpus/                  ← 10 PDFs (gitignored, fetched by script)
└── docs/
    └── DEMO_SCRIPT.md
```

---

## 8. Phased build plan

| Phase | Hours | Deliverable | Exit check |
|---|---:|---|---|
| 0 | 0.5 | `render.yaml`, `pyproject.toml`, `.env.example`, README, git init | `uvicorn` starts locally; Render Blueprint previews OK |
| 1 | 3.0 | `fetch_corpus.py` downloads 10 IIITDMJ PDFs into `data/corpus/`; `index_corpus.py` parses + chunks + embeds + writes to Postgres | Query the DB: `SELECT count(*) FROM chunks` returns ≥ 400 |
| 2 | 3.0 | `/api/chat` streaming RAG with citations; React `ChatPane` + `SourcePanel`; SSE streaming | Demo question → answer with inline `[1]`, `[2]`; click citation opens chunk |
| 3 | 4.0 | Frontend polish: Perplexity-style hover preview, source panel highlighting, shadcn theme tuned to IIITDMJ brand colours | Local dev demo shows full chat flow with citations |
| 4 | 2.0 | Structured extraction: tables, fee rows, deadlines extracted at index time; rendered as `StructuredCard` in chat | Ask about refund policy → answer contains a typed table card |
| 5 | 2.0 | Contradiction detector: at index time, scan chunks for shared numeric/policy claims and flag disagreements; `/contradictions` page and inline `ContradictionCard` | `/contradictions` lists ≥ 1 detected contradiction with the two source pages side by side |
| 6 | 1.5 | Time-aware answers: `last_updated` + `effective_from` on every doc; freshness badges; "as of 2023" filter in RAG | Ask "What was the attendance rule in 2023?" → answer cites the 2023 doc and shows the date |
| 7 | 2.0 | Live-classroom companion: `/api/companion` ephemeral session, handout upload, summary + open questions + "due tomorrow" extraction; UI shows "session will not be saved" banner | Upload a handout PDF → get a structured summary that disappears on refresh |
| 8 | 1.5 | Voice input: mic button → Speechmatics Realtime → text → RAG pipeline; Hindi+English tested | Press mic, speak Hindi, see Hinglish query → answer |
| 9 | 2.0 | Polish, deploy to Render via Blueprint, capture screenshots, write `DEMO_SCRIPT.md` | Live URL serves the frontend, backend healthy, all features reachable |

**Total: ~22 hours of focused work.** Realistic over 2 long days or 3 relaxed days.

---

## 9. Model + cost projection

### Embeddings
`intfloat/multilingual-e5-large` produces 1024-dim vectors. Local TEI on Render = free. AIMLAPI fallback = ~$0.02 / 1M tokens.

For 10 PDFs of ~30 pages each, ~500 chunks of ~500 tokens = ~250K tokens of embedding = **~$0.005 total** at AIMLAPI rates or **$0** with local TEI.

### Generation
GPT-4o-mini at ~$0.15 / 1M input tokens, $0.60 / 1M output.
Per query: 2K in + 500 out ≈ **$0.0009 / query**.
100 demo queries ≈ **$0.09**.

### Speechmatics Enhanced Realtime
$0.43 / audio hour.[1][6]
Per 30-second voice query ≈ **$0.0036**.
100 demo queries ≈ **$0.36**.

### Render (after dev)
| Resource | Cost |
|---|---:|
| Static frontend | Free |
| Backend (512 MB) | $7/mo |
| Postgres 1 GB | $19/mo (free 90-day trial available) |
| **Total after trial** | **~$26/mo or less** |

$500 Render credits = **~19 months of demo runway.** Speechmatics + AIMLAPI credit pools are independent of Render credits and not consumed by infrastructure.

### Free-credit headroom
Speechmatics Pro gives 50 concurrent Realtime sessions and 10 batch jobs/sec.[3] AIMLAPI free tier is enough for our expected 100–500 demo queries.

---

## 10. Risk register + mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Speechmatics Realtime partials mis-hear Hindi+English technical terms | Medium | Add custom dictionary with "IIITDMJ", "PDPM", "ordinances", department names, fee terms.[1] |
| Hindi query retrieves poor chunks because of generic embedding model | Low | `multilingual-e5-large` is SOTA on Hindi retrieval; benchmark on 5 sample Hindi queries before launch[20] |
| Tables flattened to prose lose fee structure | High | Phase 4 dedicated extractor uses pdfplumber + a small LLM call to recover rows; render as typed card, not prose |
| Contradiction detector produces too many false positives | Medium | Threshold on cosine similarity of claim pairs + LLM "is this a contradiction?" judge; surface only high-confidence |
| Render free Postgres trial ends mid-demo | Low | Document the cutoff date; have a fallback to SQLite + local pgvector for offline demo |
| Multilingual e5-large Docker image is heavy | Medium | Use Render `Docker` service type with `cog` or `tei` image; verify in Phase 0 |
| Live-classroom upload stores sensitive student data | Medium | Implement ephemeral session store in process memory; clear banner "this session is not saved"; auto-expire after 10 min idle |

---

## 11. Feature-to-component map

| Feature | Backend module | Frontend component | External API |
|---|---|---|---|
| Streaming RAG with citations | `services/rag.py` + `routers/chat.py` | `ChatPane`, `MessageBubble`, `SourcePanel` | AIMLAPI chat completion |
| Contradiction detector | `services/contradiction.py` + `scripts/build_contradictions.py` | `ContradictionCard`, `/contradictions` page | AIMLAPI for claim-pair judge |
| Multilingual RAG | `services/embedding.py` (multilingual-e5) | (no dedicated component) | HF TEI / local model |
| Structured extraction | `services/extractor.py` + `scripts/extract_structures.py` | `StructuredCard` | AIMLAPI for table normalisation |
| Time-aware answers | `services/rag.py` (date filter) + `models/schema.py` (`last_updated`) | `FreshnessBadge` | none |
| Live-classroom companion | `routers/companion.py` + ephemeral in-memory store | `CompanionUpload` | AIMLAPI |
| Voice input | `routers/voice.py` + `services/speechmatics_client.py` | `VoiceButton` | Speechmatics Enhanced Realtime |

---

## 12. Demo script (4-minute walkthrough)

Stored in `docs/DEMO_SCRIPT.md` after Phase 9. Plan:

1. **Cold open (0:00 – 0:20):** open `https://suchna.onrender.com`, ask "What is the attendance policy?" — answer appears with 3 citations.
2. **Multilingual (0:20 – 0:50):** click mic, speak Hindi: *"Kal kya assignment hai?"* — system transcribes, returns a structured card citing the handout PDF and class timetable.
3. **Structured (0:50 – 1:20):** type "What is the refund rule for withdrawal?" — answer contains a typed refund table card, citing the 2024 revised rule and the 2017 original.
4. **Contradiction (1:20 – 1:50):** type "What does the hostel fee section say?" — system flags: "The 2024 ordinance and the 2025 academic guidelines disagree on the hostel fee exemption rule. See both:" side-by-side cards.
5. **Time-aware (1:50 – 2:20):** type "What was the rule in 2023?" — answer cites the 2023 document with freshness badge; current rule is shown separately.
6. **Live-classroom companion (2:20 – 3:10):** upload a sample handout PDF, get structured summary with "Open questions" + "Due tomorrow" + "Key formulas"; banner reminds user nothing is saved.
7. **Voice recap (3:10 – 3:40):** one more voice query, demonstrate the streaming + partial transcript overlay.
8. **Render deploy proof (3:40 – 4:00):** show Render dashboard with the service live, cite cost, demonstrate reliability.

---

## 13. Locked decisions (do not revisit)

- **Track:** 2 — College Knowledge Assistant.
- **College:** PDPM IIITDM Jabalpur (real, public corpus).[19]
- **Name:** Suchna.
- **Corpus size:** 8–10 PDFs (hand-curated from `iiitdmj.ac.in`).
- **Embeddings:** `intfloat/multilingual-e5-large`, 1024-dim.
- **Generation:** AIMLAPI GPT-4o-mini class.
- **STT:** Speechmatics Enhanced Realtime, Batch Standard fallback.[1][2]
- **Vector store:** Postgres + pgvector on Render.[11]
- **Frontend host:** Render Static Site (free).
- **Backend host:** Render Web Service (Starter plan $7/mo).[7]
- **Admin panel:** deferred per user direction.
- **Multi-tenant / multi-college:** deferred.
- **Persistent user accounts / chat history:** not in scope.

---

## 14. References

[1] Speechmatics Speech-to-Text Models. https://docs.speechmatics.com/speech-to-text/models
[2] Speechmatics Realtime Transcription Quickstart. https://docs.speechmatics.com/speech-to-text/realtime/quickstart
[3] Speechmatics Plans. https://docs.speechmatics.com/administration/plans
[4] Speechmatics Languages. https://docs.speechmatics.com/speech-to-text/languages
[5] Speechmatics Text-to-Speech Quickstart. https://docs.speechmatics.com/text-to-speech/quickstart
[6] Speechmatics Pricing. https://www.speechmatics.com/pricing
[7] Render Web Services. https://render.com/docs/web-services
[8] Render Deploys. https://render.com/docs/deploys
[9] Render Pricing. https://render.com/pricing
[10] Render Blueprint YAML Reference. https://render.com/docs/blueprint-spec
[11] Render Postgres. https://render.com/docs/postgresql
[12] Render Key Value. https://render.com/docs/key-value
[13] InsightsLM (open-source NotebookLM alternative, UI reference). https://github.com/theaiautomators/insights-lm-public
[14] Kwipu (Graph RAG for Obsidian, multilingual retrieval reference). https://github.com/benmaster82/Kwipu
[15] SMART-CAMPUS-ASSISTANT (existing college-chatbot reference). https://github.com/Muskan-Dewangan29/SMART-CAMPUS-ASSISTANT
[16] CollegeChatbot (Streamlit + RAG reference). https://github.com/mahadev0811/CollegeChatbot
[17] Nexi-NTL (voice-driven university assistant reference). https://github.com/YEsh-DEV/nexi-ntl
[18] MTEB Leaderboard (embedding benchmark). https://huggingface.co/spaces/mteb/leaderboard
[19] IIITDM Jabalpur official site. https://www.iiitdmj.ac.in
[20] Sentence-Transformers Pretrained Models. https://docs.sentence-transformers.com/en/sentence_transformer/pretrained_models.html

---

## 15. Next concrete step

Phase 0:
1. Run `git init` in `C:\Users\arjun\Desktop\SIHih`.
2. Write `render.yaml`, `backend/pyproject.toml`, `frontend/package.json`, `.env.example`, `README.md`.
3. Confirm `uvicorn app.main:app --reload` boots.
4. Confirm `render.yaml` parses in Render Blueprint preview.

After Phase 0 is green, we move to Phase 1 (fetch the 10 IIITDMJ PDFs and index them).

## Sources

[1] https://docs.speechmatics.com/speech-to-text/models
[2] https://docs.speechmatics.com/speech-to-text/realtime/quickstart
[3] https://docs.speechmatics.com/administration/plans
[4] https://docs.speechmatics.com/speech-to-text/languages
[5] https://docs.speechmatics.com/text-to-speech/quickstart
[6] https://www.speechmatics.com/pricing
[7] https://render.com/docs/web-services
[8] https://render.com/docs/deploys
[9] https://render.com/pricing
[10] https://render.com/docs/blueprint-spec
[11] https://render.com/docs/postgresql
[12] https://render.com/docs/key-value
[13] https://github.com/theaiautomators/insights-lm-public
[14] https://github.com/benmaster82/Kwipu
[15] https://github.com/Muskan-Dewangan29/SMART-CAMPUS-ASSISTANT
[16] https://github.com/mahadev0811/CollegeChatbot
[17] https://github.com/YEsh-DEV/nexi-ntl
[18] https://huggingface.co/spaces/mteb/leaderboard
[19] https://www.iiitdmj.ac.in
[20] https://docs.sentence-transformers.com/en/sentence_transformer/pretrained_models.html
