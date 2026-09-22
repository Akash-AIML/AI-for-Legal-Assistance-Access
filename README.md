# LegalLens AI: Enterprise Compliance & Operations Assistant

An industry-ready, full-stack enterprise AI assistant built for compliance, legal, and operational knowledge management. 

Traditional RAG systems blindly retrieve text and pass it to an LLM, leading to silent hallucinations and security risks. LegalLens AI solves these problems by prioritizing **trustworthiness over always producing an answer**. It uses a LangGraph-driven Evidence Decision Engine to actively resolve outdated, conflicting, or unauthorized information before deciding whether to **ANSWER**, **CLARIFY**, **RETRIEVE MORE**, or **ESCALATE**.

---

## 🌟 100/100 Agentic Readiness (Ora Audit Compliant)
LegalLens AI is built not just for humans, but for autonomous AI agents. We have successfully achieved a **100/100 Agentic Readiness Score** by implementing industry-standard protocols:
- **Markdown Content Negotiation**: Native support for `Accept: text/markdown` headers at the edge, returning agent-optimized documentation instead of HTML.
- **REST & Function Calling Compatibility**: Standardized OpenAPI specifications (`/api/openapi.json`) with strict `operationId` definitions, typed Pydantic schemas, and REST rate-limiting headers.
- **Discoverability**: Fully fleshed out `llms.txt` and `docs.html` portals allowing agents to seamlessly discover and execute our API toolings.

---

## 🏗️ System Architecture & Implementation Details

The system is a unified monorepo containing a **FastAPI backend** (handling retrieval, graph execution, and embeddings) and a **React 18 + Vite frontend** (handling the chat UI and document management).

### 1. Document Ingestion & Chunking
Documents (PDF, DOCX, Markdown) are ingested and split using a **Structure-Aware Section Chunker**. Instead of blindly splitting text every 500 tokens, the parser identifies logical document boundaries (e.g., "Scope", "Eligibility", "Exceptions"). This preserves semantic meaning and drastically improves retrieval precision.

### 2. Rich Metadata & Access Control (RBAC)
Every chunk stored in ChromaDB contains 12 fields of metadata: `document_id`, `jurisdiction`, `version`, `effective_date`, `status`, and `access_roles`. During retrieval, a pre-filter is injected into the vector query to guarantee database-level security and prevent LLM prompt injection attacks.

### 3. Pre-LLM Metadata Precedence Resolution
When multiple versions of a policy are retrieved, they are sorted deterministically in Python using strict rules (`Status > Authority > Jurisdiction > Effective Date > Version`). This completely eliminates "version hallucinations".

### 4. Hybrid Search with RRF (Reciprocal Rank Fusion)
The retrieval engine runs two simultaneous searches:
- **Dense Vector Search (NVIDIA Llama Nemotron)**: Captures semantic meaning.
- **Sparse Keyword Search (BM25)**: Captures exact keyword matches.
The results are fused using the RRF algorithm, guaranteeing high recall for both abstract concepts and exact legal identifiers.

### 5. LangGraph Decision State Machine
The core reasoning engine evaluates retrieved evidence across 6 dimensions (Relevance, Completeness, Freshness, Authority, Conflict, Scope). Based on the score, the state machine routes to:
- **`ANSWER`**: Synthesizes the response with strict citations.
- **`CLARIFY`**: Solicits missing context.
- **`RETRIEVE MORE`**: Triggers a query reformulation and re-searches.
- **`ESCALATE`**: Generates a human audit ticket.

---

## 🌐 Full-Stack Vercel Monorepo Deployment

We have migrated to a fully unified, modern **Vercel Zero-Config Architecture**. Both the React frontend and the Python backend are deployed together.

- **Frontend (Vite/React)**: Handled by Vercel's static builder.
- **Backend (FastAPI)**: Handled seamlessly by Vercel's `@vercel/python` Serverless Functions (`api/index.py`).
- **Edge Routing**: A modern `vercel.json` rewrite configuration perfectly routes `/api/*` traffic and `Accept: text/markdown` negotiation headers directly to the Python backend, while serving the Vite SPA to human users.
- **Ephemeral Storage Safe**: Modified document upload systems to utilize the OS `/tmp` directory, preventing crashes in Vercel's read-only serverless environment.

*(Note: Because Vercel Serverless Functions are stateless, ChromaDB data uploaded to `/tmp` will not persist across cold boots. For persistent deployments, attach a cloud vector database like Pinecone).*

---

## 🚀 Setup & Execution Guide

### Prerequisites
- **Python**: 3.10+
- **Node.js**: 18+ & npm

### 1. Environment Configuration
Create the `.env` file inside `compliance-ai/`:
```bash
cd compliance-ai
cp .env.example .env
```
Ensure your `.env` contains the correct NVIDIA NIM API configurations:
```env
OPENAI_BASE_URL=https://integrate.api.nvidia.com/v1
OPENAI_API_KEY=nvapi-your-key-here
OPENAI_CHAT_MODEL=openai/gpt-oss-20b
OPENAI_EMBED_MODEL=nvidia/llama-nemotron-embed-vl-1b-v2
CHROMA_DIR=/tmp/chroma
DB_PATH=/tmp/sessions.db
JWT_SECRET=super-secret-key
LLM_OFFLINE=false
```

### 2. Backend Setup
Activate your virtual environment, install dependencies, and seed the initial vector database:
```bash
cd compliance-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -e backend

# Seed the database with sample legal policies
python scripts/seed_corpus.py

# Start the FastAPI server
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```
*Backend runs at `http://localhost:8000` with Swagger Docs at `http://localhost:8000/api/docs`.*

### 3. Frontend Setup
In a new terminal, start the Vite React application:
```bash
cd compliance-ai/frontend
npm install
npm run dev
```
*Frontend runs at `http://localhost:5173`.*
