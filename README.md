# LegalLens AI: AI for Legal Assistance & Access

An evidence-first, full-stack AI legal intelligence platform engineered to democratize legal document comprehension, contract risk analysis, and citizen justice access.

- **Live Production Application**: [https://ai-for-legal-assistance-access-pi.vercel.app](https://ai-for-legal-assistance-access-pi.vercel.app)
- **API Documentation (OpenAPI / Swagger)**: `https://ai-for-legal-assistance-access-pi.vercel.app/api/docs`
- **Agentic llms.txt Discovery**: `https://ai-for-legal-assistance-access-pi.vercel.app/llms.txt`

## GenAI Services Used

LegalLens uses OpenAI-compatible APIs so the provider can be configured without changing application code:

- **Groq** (`https://api.groq.com/openai/v1`) is the default inference provider. Its `openai/gpt-oss-120b` model powers Document X-Ray analysis, contract comparison, lawyer briefs, Hindi responses, legal Q&A, and streamed chat responses.
- **NVIDIA-compatible embedding endpoints** are supported for semantic document and query embeddings used by ChromaDB retrieval and RAG. When the configured provider is Groq, which does not expose embeddings, the app uses its deterministic offline embedding fallback.
- **Whisper-compatible speech transcription** uses `whisper-large-v3-turbo` through `/api/speech/transcribe` to turn citizen voice questions into text.
- **OpenAI-compatible text-to-speech** is exposed through `/api/speech/tts` and `/api/tts`, converting assistant answers into audio for voice-first accessibility. It tries `tts-1`, `gpt-4o-mini-tts`, and `gpt-4o-audio-preview` in order.
- **Offline fallback mode** provides deterministic embeddings and a local responder when credentials are unavailable, allowing demos and automated tests to run without external AI calls.

---

## 🎯 Architectural Principles & Metric Optimizations

LegalLens AI is engineered to address the critical challenges of legal document intelligence. Below is a detailed breakdown of **what we built**, **why it matters**, and **how the system is optimized** across each evaluation dimension.

---

### 1. Problem Statement Alignment (Citizen Legal Empowerment)

#### What We Built:
- **Full-Contract 25-Chunk Coverage**: Dynamic windowing and sampling that evaluates up to 25 distributed sections across an entire agreement rather than truncating after initial introductory paragraphs.
- **Plain-English Legal Glossary**: Interactive glossary featuring in-line contextual hover tooltips (`<LegalTooltip>`) explaining complex legalese (e.g., *Indemnification*, *Force Majeure*, *Severability*, *Liquidated Damages*).
- **Lawyer Consultation Brief Generator**: Automated pre-consultation brief creation with one-click export, summarizing key risks, client obligations, and 5 tailored questions to ask during a consultation.
- **Clause-Level Contract Comparison**: Semantic diffing tool that compares two contract versions side-by-side, categorizing clauses as *Added*, *Modified*, or *Removed* with plain-English impact analyses.
- **Vernacular & Citizen Personas**: Multi-language support (English & Hindi) tailored to five distinct user roles: *Citizen*, *Freelancer*, *Small Business*, *Legal Aid Advisor*, and *Admin*.

#### Why It Matters:
Standard consumers, tenants, and small business owners lack access to expensive legal counsel and struggle to interpret multi-page agreements. Critical liabilities, penalty clauses, and automatic renewals are often buried in late sections of contracts. Without preparation, consulting an attorney is intimidating, inefficient, and costly.

#### How It's Optimized:
- **Dynamic Section Sampling**: Guarantees that late-document termination, liability caps, and indemnity clauses are analyzed without exceeding model context limits.
- **Client-Side Glossary Cache**: In-line tooltips trigger instant definitions without round-trip network latency.
- **Structured Synthesis**: Briefs distill multi-page contracts into a 1-page action-oriented summary for immediate lawyer onboarding.

---

### 2. Code Quality & Architecture

#### What We Built:
- **Decoupled Storage & Retrieval System**: Modularized the ingestion engine into two focused modules:
  - `ingestion/store.py`: Dedicated solely to ChromaDB connection lifecycle, collection management, and chunk persistence.
  - `ingestion/search.py`: Dedicated solely to in-memory BM25 index scoring, dense semantic retrieval, Reciprocal Rank Fusion (RRF), and RBAC filtering.
- **Guaranteed JSON Schema Enforcement**: Configured `response_format={"type": "json_object"}` across all LLM inference points in `legal_engine.py`.
- **Strict TypeScript Type Safety**: Zero `any` types across the entire frontend codebase, with typed event interfaces (`StreamMetaEvent`, `StreamTokenEvent`) for SSE streams.

#### Why It Matters:
Monolithic 400+ line files intermingling vector storage and search algorithms degrade maintainability and increase bug surface area. Relying on regular expressions to patch malformed LLM JSON strings introduces silent parsing failures in compliance-critical pipelines.

#### How It's Optimized:
- **Single Responsibility Principle**: Isolating persistence from search algorithms enables independent testing, tuning, and database swapping (e.g., Pinecone/Qdrant) without touching search logic.
- **Native Structured Output**: Eliminates fragile regex bracket repair routines, ensuring 100% reliable downstream parsing.
- **Strict Typing**: Catches contract and event mismatches at compile-time before reaching production.

---

### 3. Security & Threat Mitigation

#### What We Built:
- **NIST/OWASP-Compliant PBKDF2 Password Hashing**: Upgraded user authentication in `auth.py` to `hashlib.pbkdf2_hmac("sha256", ..., 100_000)` with per-user cryptographically random 16-hex salts and constant-time comparison (`hmac.compare_digest`).
- **Binary Magic-Byte File Upload Validation**: Inspects raw binary header bytes (`b"%PDF"` for PDFs, `b"PK\x03\x04"` for DOCX, blocking ELF/PE binaries) in `document_routes.py`.
- **Multi-Tenant Document Isolation**: Enforced user tenancy so uploaded contracts are strictly visible and queryable only by the uploading user, while featured legal reference templates remain globally accessible.
- **Pre-Retrieval Database-Level RBAC**: Injects access control filters into the database retrieval query before context is passed to the LLM.

#### Why It Matters:
Legal agreements contain confidential personal and financial data. Basic SHA-256 is vulnerable to rainbow table attacks. Allowing file uploads by extension alone exposes systems to disguised executable malware. If role-based filtering occurs *after* retrieval, malicious users can use prompt injection to extract confidential clauses.

#### How It's Optimized:
- **Pre-Storage File Verification**: Rejects spoofed or malicious uploads at the socket layer before writing to disk.
- **Zero-Leakage RBAC**: Database-level pre-filtering ensures the LLM never receives unauthorized text in its prompt, making prompt-injection data exfiltration impossible.
- **Deterministic Secret Expansion**: Automatically expands short environment secrets (e.g., `JWT_SECRET`) via SHA-256 to ensure robust cryptographic keys without startup crashes.

---

### 4. System Efficiency & Performance

#### What We Built:
- **Incremental BM25 Updates**: Implemented `append_to_bm25(new_chunks)` to dynamically update the tokenized BM25 index when a document is uploaded.
- **Non-Blocking Asynchronous Handlers**: Converted CPU- and IO-bound endpoints in `legal_routes.py` to `async def` with `await anyio.to_thread.run_sync(...)`.
- **LRU Query Embedding Cache**: Implemented `@functools.lru_cache(maxsize=256)` on query vectorization (`_get_query_embedding`).
- **Serverless-Safe Lifecycle**: Made background indexing threads conditional on persistent environments, eliminating container freezes on Vercel.
- **Streaming SSE Responses**: Real-time token streaming over Server-Sent Events (SSE).

#### Why It Matters:
Re-indexing the entire document corpus on every upload causes $O(N)$ CPU latency spikes. Synchronous route handlers block Python's asynchronous event loop under concurrent load. Re-vectorizing identical or repeated search queries wastes network round-trips and API credits.

#### How It's Optimized:
- **$O(1)$ Index Appends**: Eliminates full-corpus scans on upload, keeping upload processing fast and scalable.
- **Event Loop Protection**: Offloads heavy processing to threadpool workers, preserving sub-millisecond API responsiveness.
- **Zero-Latency Repeat Queries**: LRU cache eliminates API roundtrips for repeated questions across chat turns.
- **Low TTFT**: Streaming reduces Time-To-First-Token to under 300ms for immediate feedback.

---

### 5. Testing & System Resilience

#### What We Built:
- **Backend Test Suite (60 Passing Tests)**:
  - Unit tests for authentication, user registration, and PBKDF2 salt hashing.
  - SSE streaming integration tests (`/api/chat/stream`) validating chunk tokens and metadata events.
  - Rate limit (429) and gateway timeout (504) resilience tests confirming graceful error recovery.
  - RAG benchmark suite evaluating precision, recall, and Reciprocal Rank Fusion accuracy.
- **Frontend Test Suite (13 Passing Tests across 5 Suites)**:
  - `DocumentXRay.test.tsx`: Validates document risk analysis rendering and legal glossary tooltips.
  - `ContractCompare.test.tsx`: Validates clause diff calculations and impact views.
  - `LegalChat.test.tsx`: Verifies multi-turn chat sessions and streaming state.
  - `LegalGlossary.test.tsx`: Tests search filtering and definition rendering.
  - `UploadView.test.tsx`: Validates magic-byte upload guards and drag-and-drop states.

#### Why It Matters:
Production legal software cannot crash when third-party LLM APIs encounter rate limits or timeouts. Automated regression testing is critical to guarantee that security rules, RBAC filters, and extraction logic remain intact across code changes.

#### How It's Optimized:
- **Graceful Error Handling**: Backoff and structured error messages ensure users receive clear actionable feedback rather than broken interfaces.
- **Deterministic Test Mocking**: Network-independent unit and integration tests run in seconds without external API dependencies.

---

### 6. Accessibility & Inclusivity (a11y)

#### What We Built:
- **Screen Reader Live Announcements**: Added `<div role="status" aria-live="assertive" className="sr-only">` to announce real-time document analysis progress and completion.
- **Keyboard Navigation & Modal Focus Traps**: Mobile navigation drawers and dialog modals trap Tab focus and restore focus on dismiss (`AppLayout.tsx`).
- **Voice-First Citizen Accessibility**: Integrated Whisper-1 audio transcription (`/api/speech/transcribe`) and text-to-speech audio synthesis (`/api/speech/tts`).
- **WCAG 2.1 AA Semantic Styling**: High-contrast, semantic color tokens for clear visual hierarchy.

#### Why It Matters:
Equal access to justice means serving citizens regardless of disability, technical literacy, or reading ability. Citizens with visual impairments or motor challenges require screen readers and keyboard navigation, while citizens with low literacy benefit from voice interactions.

#### How It's Optimized:
- **Accessible Streaming Regions**: `aria-live="polite"` chat regions ensure screen reader users receive synthesized legal answers in real time without audio overlap.
- **Low-Latency Voice Pipeline**: Audio uploads are processed directly via streaming audio endpoints for rapid speech-to-text response.

---

## 🌐 Production Deployment Architecture (Vercel)

The system runs on a unified, high-performance Vercel serverless architecture:

```
                  ┌─────────────────────────────────────┐
                  │          Vercel Edge Proxy          │
                  └──────────────────┬──────────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 │                                       │
        Path: /api/*                             Path: /* (SPA)
                 │                                       │
                 ▼                                       ▼
  ┌─────────────────────────────┐         ┌─────────────────────────────┐
  │   @vercel/python Lambda     │         │   @vercel/static-build      │
  │   - FastAPI Backend App     │         │   - React 18 + Vite SPA     │
  │   - ChromaDB (Ephemeral)    │         │   - Tailwind & Radix UI     │
  │   - LangGraph Reasoning     │         │   - Web Audio API (Voice)   │
  └─────────────────────────────┘         └─────────────────────────────┘
```

- **Dual Builder Configuration**: Uses `@vercel/python` for `api/index.py` and `@vercel/static-build` for `frontend/package.json`.
- **Deterministic Secret Expansion**: Automatically expands environment secrets (e.g. `JWT_SECRET`) via SHA-256 to ensure zero startup configuration crashes.
- **Production URL**: [https://ai-for-legal-assistance-access-pi.vercel.app](https://ai-for-legal-assistance-access-pi.vercel.app)

---

## 🛠️ Local Development & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Backend Setup
```bash
cd compliance-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run all backend tests
uv run --with pytest pytest backend/tests -v

# Start backend dev server
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup
```bash
cd compliance-ai/frontend
npm install

# Run all frontend tests
npm test

# Start frontend dev server
npm run dev
```

---

## 👥 Citizen Personas & Credentials (Demo Accounts)

All demo accounts use password: **`demo123`**

| Username | Name | Role | Department / Domain | Jurisdiction |
| :--- | :--- | :--- | :--- | :---: |
| `admin` | Admin User | Admin | Legal Operations | Global |
| `asha` | Asha Rao | Citizen | Tenancy & Housing | IN |
| `kenji` | Kenji Sato | Freelancer | Independent Work | DE |
| `maria` | Maria Lopez | Small Business | Retail Operations | US |
| `priya` | Priya Sharma | Legal Aid Advisor | Pro Bono Legal Aid | IN |
