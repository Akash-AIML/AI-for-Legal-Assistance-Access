# Enterprise Compliance & Operations AI Assistant

An industry-ready, full-stack enterprise AI assistant built for compliance, legal, and operational knowledge management. Operating on internal organizational documents, the system prioritizes **trustworthiness over always producing an answer**, actively resolving outdated, conflicting, or unauthorized information before deciding whether to **ANSWER**, **CLARIFY**, **RETRIEVE MORE**, or **ESCALATE**.

---

## 🌐 Live Demos & Production Deployments

| Component | URL / Endpoint | Description |
| :--- | :--- | :--- |
| **🚀 Production Web App (Custom Domain)** | [https://epcomp.akashg.me/](https://epcomp.akashg.me/) | Live React SPA with Glassmorphism UI & Dual-tier TTS |
| **⚡ Vercel Frontend Deployment** | [https://navigate-labs-hackathon.vercel.app/](https://navigate-labs-hackathon.vercel.app/) | Vercel Edge SPA deployment |
| **⚙️ Azure Container App Backend API Docs** | [https://compliance-ai-backend.agreeableocean-d133ab66.eastasia.azurecontainerapps.io/docs](https://compliance-ai-backend.agreeableocean-d133ab66.eastasia.azurecontainerapps.io/docs) | Live FastAPI Swagger UI REST API Documentation |
| **🩺 Backend Health Endpoint** | [https://compliance-ai-backend.agreeableocean-d133ab66.eastasia.azurecontainerapps.io/api/health](https://compliance-ai-backend.agreeableocean-d133ab66.eastasia.azurecontainerapps.io/api/health) | System health status (16 docs, 283 chunks online) |

---

## 📌 Executive Summary & Key Achievements

Traditional Retrieval-Augmented Generation (RAG) systems blindly retrieve context and pass it to an LLM, leading to silent hallucinations, version confusion, and security risks. This assistant solves these problems with a **LangGraph-driven Evidence Decision Engine**:

1. **Structure-Aware Document Ingestion & Section Chunking**: Keeps logical sections (Scope, Eligibility, Procedure, Exceptions) intact rather than naively splitting by fixed token windows.
2. **Rich 12-Field Metadata Extraction**: Tracks `document_id`, `title`, `section`, `department`, `jurisdiction`, `version`, `effective_date`, `review_date`, `status` (`ACTIVE`, `SUPERSEDED`, `REVIEW_OVERDUE`, `DRAFT`), `authority`, and `access_roles`.
3. **Pre-LLM Metadata Resolution**: Resolves version collisions (e.g., Policy v2 vs Policy v4) deterministically prior to LLM reasoning using strict metadata precedence rules (`Status > Authority > Jurisdiction > Effective Date > Version`).
4. **Permission-Aware (RBAC) Retrieval**: Applies role-based filters at search time (`Employee`, `Manager`, `HR`, `Compliance`, `Admin`), preventing unauthorized document retrieval at the database query level.
5. **Hybrid Vector + Keyword Search**: Combines ChromaDB dense semantic retrieval with BM25 keyword matching via Reciprocal Rank Fusion (RRF) for precise clause lookups (`POL-HR-104`, `ISO 27001`).
6. **6-Dimension Evidence Assessment Engine**: Evaluates candidate chunks across Relevance, Completeness, Freshness, Authority, Conflict, and Scope to output explicit evidence states (`SUPPORTED`, `AMBIGUOUS`, `INSUFFICIENT_EVIDENCE`, `CONFLICTING_EVIDENCE`, `OUTDATED_EVIDENCE`, `RESTRICTED`).
7. **Controlled LangGraph Decision Routing**: State-machine workflow that routes queries to:
   - **`ANSWER`**: Grounded generation with strict source citations.
   - **`CLARIFY`**: Solicits missing context (e.g., user jurisdiction) before retrying.
   - **`RETRIEVE MORE`**: Query expansion and bounded re-retrieval.
   - **`ESCALATE`**: Generates audit trails and escalates unresolved conflicts or high-risk queries to human reviewers.
8. **Interactive Full-Stack Web Interface**:
   - Modern dark-mode UI (React 18 + Tailwind CSS) with decision status badges, clickable citation drawers, and native speech interaction (STT/TTS).
   - Knowledge Management & Escalation Dashboard for uploading, marking documents `ACTIVE`/`SUPERSEDED`, and inspecting human escalation tickets.

---

## 🔄 System Architecture & Workflow Structure

```text
                             ┌───────────────────────────────────┐
                             │       User Query / Speech         │
                             └─────────────────┬─────────────────┘
                                               │
                                               ▼
                             ┌───────────────────────────────────┐
                             │  1. Pre-Retrieval Understanding  │
                             │  - Extract Entity Constraints     │
                             │  - Apply User Profile/RBAC Filter │
                             └─────────────────┬─────────────────┘
                                               │
                                               ▼
                             ┌───────────────────────────────────┐
                             │  2. Hybrid Retrieval Pipeline     │
                             │  - Dense Retrieval (ChromaDB)     │
                             │  - Sparse Keyword Retrieval (BM25)│
                             │  - Reciprocal Rank Fusion (RRF)   │
                             └─────────────────┬─────────────────┘
                                               │
                                               ▼
                             ┌───────────────────────────────────┐
                             │  3. Pre-LLM Metadata Resolution   │
                             │  - Active vs Superseded Filtering │
                             │  - Authority & Date Precedence    │
                             └─────────────────┬─────────────────┘
                                               │
                                               ▼
                             ┌───────────────────────────────────┐
                             │ 4. Evidence Assessment Classifier │
                             │ Evaluates 6 Evidence Dimensions:  │
                             │ Relevance, Completeness, Freshness│
                             │ Authority, Conflict & Scope       │
                             └─────────────────┬─────────────────┘
                                               │
                                               ▼
                             ┌───────────────────────────────────┐
                             │    5. LangGraph Decision Router   │
                             └─────────────────┬─────────────────┘
                                               │
            ┌──────────────────────┬───────────┴───────────┬──────────────────────┐
            │                      │                       │                      │
            ▼                      ▼                       ▼                      ▼
     ┌─────────────┐        ┌─────────────┐         ┌─────────────┐        ┌─────────────┐
     │   ANSWER    │        │   CLARIFY   │         │RETRIEVE MORE│        │  ESCALATE   │
     │  Grounded   │        │ Solicit     │         │ Bounded Re- │        │ Human Ticket│
     │ Citation    │        │ Missing     │         │ Query &     │        │ Audit Log   │
     │ Generation  │        │ Context     │         │ Retry Search│        │ Generation  │
     └──────┬──────┘        └──────┬──────┘         └──────┬──────┘        └──────┬──────┘
            │                      │                       │                      │
            └──────────────────────┴───────────┬───────────┴──────────────────────┘
                                               │
                                               ▼
                             ┌───────────────────────────────────┐
                             │   Full-Stack UI / Voice Output    │
                             │   Chat, Citations, Admin Trace    │
                             └───────────────────────────────────┘
```

### Step-by-Step Data Flow

1. **User Query & Context Ingestion**: The query is submitted via the React web UI or captured via browser Speech-to-Text. The user's role (`Employee`, `Manager`, `HR`, `Admin`) and existing conversation session state are attached.
2. **Permission-Aware Query Understanding**: Role-based access filters (`access_roles IN [UserRole, "All"]`) are automatically injected into the search request before vector search execution to prevent unauthorized information access.
3. **Hybrid Search & Fusion**: Dense semantic vector search (ChromaDB) and sparse keyword search (BM25) retrieve initial candidate chunks. Scores are fused using Reciprocal Rank Fusion (RRF).
4. **Deterministic Pre-LLM Metadata Precedence**: Version collisions (e.g. Policy v2 vs Policy v4) and document status conflicts are resolved deterministically based on priority:
   $$\text{Status (Active > Superseded)} \rightarrow \text{Authority} \rightarrow \text{Jurisdiction} \rightarrow \text{Effective Date} \rightarrow \text{Version}$$
5. **Multi-Dimensional Evidence Assessment**: The Candidate Evidence Assessor evaluates chunks across 6 dimensions to output an explicit evidence classification (`SUPPORTED`, `AMBIGUOUS`, `INSUFFICIENT_EVIDENCE`, `CONFLICTING_EVIDENCE`, `OUTDATED_EVIDENCE`, `RESTRICTED`).
6. **LangGraph State Machine Execution**:
   - **`ANSWER`**: Grounded answer generation using verified active sources with inline citations.
   - **`CLARIFY`**: Solicits missing context parameters (e.g., country of employment) when queries are ambiguous.
   - **`RETRIEVE MORE`**: Triggers targeted query reformulation for a single bounded retry attempt.
   - **`ESCALATE`**: Generates a human review escalation ticket (`ESC-XXXXX`) logged to the database for compliance review.
7. **UI Render & Speech Synthesis**: The final response is delivered to the React frontend with dynamic decision badges, expandable source drawers, and browser Text-to-Speech playback.

---

## 📂 Project Directory Structure

```text
Hackathon/
├── PLAN.md                               # Architectural plan and technical specification
├── README.md                             # Global project documentation
└── compliance-ai/                        # Core Application Root
    ├── .env                              # Environment configuration (API keys, models, DB paths)
    ├── .env.example                      # Template environment file
    ├── pyproject.toml                    # Python project dependencies and build configuration
    │
    ├── backend/                          # FastAPI Backend Application
    │   └── src/
    │       ├── main.py                   # FastAPI server entry point & CORS configuration
    │       ├── config.py                 # Pydantic environment configuration settings
    │       ├── auth.py                   # JWT Authentication & RBAC role handling
    │       ├── models.py                 # Pydantic schemas (User, Document, Decision, Escalation)
    │       ├── llm.py                    # OpenAI-compatible API gateway client & offline fallback generator
    │       │
    │       ├── api/                      # REST API Endpoints
    │       │   ├── auth_routes.py        # Login & demo user authentication
    │       │   ├── chat_routes.py        # Streaming chat & decision engine execution endpoint
    │       │   ├── document_routes.py    # Document upload, listing, status toggling & re-indexing
    │       │   ├── escalation_routes.py  # Human escalation creation & admin ticket management
    │       │   └── speech_routes.py      # Speech-to-Text & Text-to-Speech service endpoints
    │       │
    │       ├── ingestion/                # Document Ingestion Pipeline
    │       │   ├── parser.py             # Document parsing (PDF, DOCX, TXT, MD)
    │       │   ├── chunker.py            # Section-aware structural text chunking
    │       │   ├── store.py              # ChromaDB vector store wrapper & metadata indexer
    │       │   └── ingestor.py           # Unified document ingestion orchestrator
    │       │
    │       ├── retrieval/                # Search & Fusion Engine
    │       │   └── evidence.py           # Hybrid Dense (Chroma) + BM25 search with RRF reranking
    │       │
    │       ├── graph/                    # LangGraph Decision Workflow Engine
    │       │   ├── state.py              # Graph state schema (query, context, evidence, decision)
    │       │   ├── assessor.py           # 6-Dimension Evidence Assessment logic
    │       │   ├── nodes.py              # LangGraph node implementations (Assess, Decide, Answer, Clarify, Escalate)
    │       │   └── builder.py            # StateGraph construction & compiled workflow runner
    │       │
    │       ├── memory/                   # Session & Conversation State Management
    │       └── evaluation/               # Golden question benchmark & evaluation harness
    │
    ├── frontend/                         # React Frontend Application
    │   ├── index.html                    # HTML web page container
    │   ├── vite.config.js                # Vite build tool setup & proxy configuration
    │   ├── tailwind.config.js            # Tailwind CSS design system tokens
    │   └── src/
    │       ├── main.jsx                  # Application React DOM root
    │       ├── App.jsx                   # Main layout container & view switcher
    │       ├── api.js                    # Axios API client with auto-attached JWT auth headers
    │       ├── index.css                 # Base glassmorphism styling & custom CSS rules
    │       └── components/
    │           ├── Login.jsx             # Role-based demo login selector (Employee, Manager, HR, Admin)
    │           ├── Chat.jsx              # Main chat view, decision indicators, voice controls & sources drawer
    │           └── Admin.jsx             # Document management, active/superseded toggling & escalation review
    │
    ├── scripts/                          # Utility & Data Seeding Scripts
    │   ├── seed_corpus.py                # Seeds realistic enterprise documents (Leave, Travel, Security, HR policies)
    │   └── reembed.py                    # Triggers vector store re-indexing
    │
    └── tests/                            # Automated Testing Suite
        └── test_decision.py              # Pytest unit tests for LangGraph state machine decision routing
```

---

## 🛠️ Methods, Algorithms & Architectural Rationale

### 1. LangGraph Decision State Machine Engine
* **Method**: Implemented using a directed state graph (`StateGraph`) with conditional routing logic based on candidate evidence scores.
* **Why**: Linear chains cannot handle branching states or graceful degradation. LangGraph allows explicit state representation (`ANSWER`, `CLARIFY`, `RETRIEVE MORE`, `ESCALATE`) and enforces bounded execution loops (e.g., maximum 1 retrieval retry) to eliminate endless hallucination loops.

### 2. Pre-LLM Version & Authority Resolution
* **Algorithm**: Pre-retrieval sorting of candidate documents using deterministic metadata priority:
  $$\text{Priority} = \text{Status (Active > Superseded)} \rightarrow \text{Authority} \rightarrow \text{Jurisdiction} \rightarrow \text{Effective Date} \rightarrow \text{Version}$$
* **Why**: LLMs frequently struggle with numeric version comparison and temporal logic. Resolving document precedence deterministically at the database level eliminates version hallucinations before the context ever reaches the LLM.
* **Version-Based Question Execution Modes**:
  - **Operational Mode (Default)**: Standard queries (*"What is the leave limit?"*) resolve automatically to the `ACTIVE` policy (e.g. v2: 4 days/month), while ignoring superseded versions (e.g. v1: 2 leaves/month).
  - **Comparative Mode (Explicit Version Query)**: Comparative queries (*"What changed between v1 and v2?"* or *"What did v1 say vs v2?"*) retrieve both version chunks to produce a grounded comparison contrasting historical rules with active ones.
  - **Conflict Escalation Mode**: Contradictions between two *currently active* policies trigger `CONFLICTING_EVIDENCE` $\rightarrow$ `ESCALATE` ticket rather than guessing.

### 3. Hybrid Dense + Keyword Retrieval with Reciprocal Rank Fusion (RRF)
* **Algorithm**: Computes combined chunk score from dense cosine similarity ($S_{\text{dense}}$) and BM25 sparse keyword rank ($R_{\text{sparse}}$):
  $$RRF(d) = \frac{1}{60 + R_{\text{dense}}(d)} + \frac{1}{60 + R_{\text{BM25}}(d)}$$
* **Why**: Vector embeddings capture semantic meaning ("leave rollover policy") but often miss exact legal clause references (`POL-HR-104`, `ISO 27001`). Hybrid fusion guarantees high recall for both abstract and precise queries.

### 4. 6-Dimension Evidence Assessment Classifier
* **Method**: Multi-factor classification evaluating relevance score, missing required entity constraints (e.g. employee jurisdiction), document freshness status, authority level, and cross-document agreement.
* **Why**: Evaluating evidence *before* passing it to the generator prevents the model from synthesizing answers out of low-quality or conflicting context.

### 5. Security & Permission-Aware Retrieval (RBAC Filter)
* **Method**: Access filtering integrated directly into vector store queries:
  $$\text{Filter} = \{ \text{access\_roles}: \{ \text{\$in}: [\text{UserRole}, \text{"All"}] \} \}$$
* **Why**: Filtering post-retrieval wastes vector search capacity and increases security risks. Filtering at query time guarantees zero leaks of confidential documents (e.g., executive compensation policies).

---

## 🤖 Models & Provider Configurations

The assistant is built to run seamlessly with any **OpenAI-compatible LLM Gateway** or fully offline.

| Component | Default Model / Technology | Configuration Key (`.env`) | Rationale |
| :--- | :--- | :--- | :--- |
| **Reasoning & Generation LLM** | `gpt-4.1-nano` / OpenAI Compatible | `OPENAI_CHAT_MODEL`, `OPENAI_BASE_URL` | Fast instruction following for structured decision evaluation & grounded answer generation with citations. |
| **Semantic Embeddings** | `text-embedding-3-small` / OpenAI Compatible | `OPENAI_EMBED_MODEL` | High-density 1536-dim semantic representation for ChromaDB vector indexing. |
| **Sparse Keyword Search** | BM25 (Rank-BM25 / Tokenizer) | Built-in | Fast, dependency-free exact keyword matching for clause codes and document IDs. |
| **Speech STT / TTS** | Web Speech API (`SpeechRecognition` & `SpeechSynthesis`) | Browser Native | Native browser implementation provides zero latency, zero server cost, and works without external credentials. |
| **Offline Demonstration Mode** | Mock Fallback Decision Engine | `LLM_OFFLINE=true` | Built-in fallback system allows complete full-stack execution and testing even without external internet or active API credentials. |

---

## 🚀 Setup & Execution Guide

### Prerequisites
- **Python**: 3.10+
- **Node.js**: 18+ & npm

---

### Step 1: Environment Configuration
Create or inspect the `.env` file inside `compliance-ai/`:

```bash
cd compliance-ai
cp .env.example .env
```

Ensure `.env` contains your OpenAI-compatible gateway parameters:
```env
OPENAI_BASE_URL=https://apidev.navigatelabsai.com/
OPENAI_API_KEY=sk-your-api-key
OPENAI_CHAT_MODEL=gpt-4.1-nano
OPENAI_EMBED_MODEL=text-embedding-3-small

CHROMA_DIR=./backend/data/chroma
DB_PATH=./backend/data/sessions.db
JWT_SECRET=super-secret-key-change-in-prod
LLM_OFFLINE=false
```

---

### Step 2: Backend Setup & Seed Data

1. Activate virtual environment and install backend dependencies:
```bash
cd compliance-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -e backend
```

2. Seed initial enterprise policy documents into ChromaDB & BM25 index:
```bash
python scripts/seed_corpus.py
```
*This populates realistic sample documents covering India Leave Policy v4 (Active), India Leave Policy v2 (Superseded), Germany Work Policy, IT Security Guidelines, Travel Expenses, and Restricted HR Executive Files.*

3. Start the FastAPI backend server:
```bash
uvicorn backend.src.main:app --host 0.0.0.0 --port 8000 --reload
```
*Backend runs at `http://localhost:8000` (API Docs available at `http://localhost:8000/docs`).*

---

### Step 3: Frontend Setup & Execution

1. Open a new terminal, navigate to `frontend/` and install packages:
```bash
cd compliance-ai/frontend
npm install
```

2. Start the Vite development server:
```bash
npm run dev
```
*Frontend runs at `http://localhost:5173`.*

---

### Step 4: Verification & Testing

To run the automated decision engine test suite:
```bash
cd compliance-ai
pytest tests/test_decision.py -v
```

---

## 🧪 Demonstration Walkthrough & Test Scenarios

Log in using demo roles in the frontend UI (`http://localhost:5173`) to test the 4 core decisions:

1. **`ANSWER` Decision**:
   - *User Role*: Employee (India)
   - *Query*: *"What is the annual leave carry forward policy for India?"*
   - *Expected Outcome*: Returns grounded answer citing **India Annual Leave Policy v4 (§4.2)** with `Active` status badge. Resolves conflict with superseded v2 policy automatically.

2. **`CLARIFY` Decision**:
   - *User Role*: Employee (General)
   - *Query*: *"Can I carry forward unused annual leave?"*
   - *Expected Outcome*: Engine detects missing required entity (`jurisdiction`) and responds asking: *"Which country are you employed in (e.g., India or Germany)?"*

3. **`ESCALATE` Decision**:
   - *User Role*: Employee
   - *Query*: *"What is the exact executive bonus formula for 2026?"*
   - *Expected Outcome*: Restricted policy access or ambiguous information triggers an **`ESCALATE`** action, creating a ticket (`ESC-XXXXX`) visible in the Admin Escalation Dashboard.

4. **`RESTRICTED` Filter**:
   - *User Role*: Standard Employee vs HR Manager
   - *Query*: *"Show executive severance policy"*
   - *Expected Outcome*: Standard Employee retrieves 0 restricted chunks; HR Manager accesses authorized confidential documentation.

---

## 📄 License & Maintainers

Built as an enterprise-grade AI solution for compliance, auditability, and trustworthy organizational intelligence.
