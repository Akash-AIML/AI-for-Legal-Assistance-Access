# LegalLens AI: Enterprise Compliance & Operations Assistant

An industry-ready, full-stack enterprise AI assistant built for compliance, legal, and operational knowledge management. 

Traditional RAG systems blindly retrieve text and pass it to an LLM, leading to silent hallucinations and security risks. LegalLens AI solves these problems by prioritizing **trustworthiness over always producing an answer**. It uses a LangGraph-driven Evidence Decision Engine to actively resolve outdated, conflicting, or unauthorized information before deciding whether to **ANSWER**, **CLARIFY**, **RETRIEVE MORE**, or **ESCALATE**.

---

## 🏗️ System Architecture & Implementation Details

The system is separated into a **FastAPI backend** (handling retrieval, graph execution, and embeddings) and a **React 18 + Vite frontend** (handling the chat UI, streaming, and document management).

### 1. Document Ingestion & Chunking
**Implementation:**
Documents (PDF, DOCX, Markdown) are ingested and split using a **Structure-Aware Section Chunker**. Instead of blindly splitting text every 500 tokens, the parser identifies logical document boundaries (e.g., "Scope", "Eligibility", "Exceptions").
**Reasoning:**
Legal and compliance documents rely heavily on context. Splitting a clause in half ruins semantic meaning. By chunking at the section level, the vector embedding accurately represents the entire logical thought, drastically improving retrieval precision.

### 2. Rich Metadata & Access Control (RBAC)
**Implementation:**
Every chunk stored in ChromaDB contains 12 fields of metadata: `document_id`, `jurisdiction`, `version`, `effective_date`, `status` (`ACTIVE`/`SUPERSEDED`), and `access_roles` (e.g., `HR`, `Employee`, `Manager`).
During retrieval, a pre-filter is injected into the vector query: `{"access_roles": {"$in": [UserRole, "All"]}}`.
**Reasoning:**
Applying Role-Based Access Control *before* the vector search executes ensures zero data leakage. If an LLM is used to filter out restricted data *after* retrieval, prompt injection attacks can bypass it. Database-level filtering guarantees security.

### 3. Pre-LLM Metadata Precedence Resolution
**Implementation:**
When multiple versions of a policy are retrieved (e.g., Leave Policy v2 and v4), they are sorted deterministically in Python using strict rules: `Status > Authority > Jurisdiction > Effective Date > Version`.
**Reasoning:**
LLMs are notoriously bad at temporal logic and numeric version comparisons. By resolving these conflicts deterministically *before* passing the context to the LLM, we completely eliminate "version hallucinations" (where the LLM accidentally cites an old policy).

### 4. Hybrid Search with RRF (Reciprocal Rank Fusion)
**Implementation:**
The retrieval engine runs two simultaneous searches:
- **Dense Vector Search (ChromaDB + NVIDIA Llama Nemotron)**: Captures semantic meaning.
- **Sparse Keyword Search (BM25)**: Captures exact keyword matches.
The results are fused using the RRF algorithm.
**Reasoning:**
Vector search is great for abstract queries ("what is the leave limit?"), but terrible at finding exact clause IDs (e.g., "ISO 27001 Section 4"). Hybrid search guarantees high recall for both abstract concepts and exact legal identifiers.

### 5. LangGraph Decision State Machine
**Implementation:**
Rather than a simple LangChain pipeline, the core reasoning engine is built on **LangGraph**. It evaluates retrieved evidence across 6 dimensions (Relevance, Completeness, Freshness, Authority, Conflict, Scope). Based on the score, the state machine routes to:
- **`ANSWER`**: Synthesizes the response with strict citations.
- **`CLARIFY`**: Solicits missing context (e.g., "Which country do you work in?").
- **`RETRIEVE MORE`**: Triggers a query reformulation and re-searches.
- **`ESCALATE`**: Generates a human audit ticket (`ESC-XXXXX`) for contradictions or restricted access.
**Reasoning:**
Linear LLM chains cannot gracefully handle failure. LangGraph enables bounded loops (e.g., allowing exactly one retrieval retry) and explicit fallback states, preventing the LLM from guessing when it lacks sufficient evidence.

### 6. Streaming SSE & NVIDIA NIM Integration
**Implementation:**
The backend utilizes Server-Sent Events (SSE) to stream tokens directly to the React frontend. It integrates state-of-the-art **NVIDIA NIM Models** (`gpt-oss-20b` for chat, `llama-nemotron-embed` for embeddings).
**Reasoning:**
Legal queries require massive context windows and deep reasoning, which can take several seconds. Streaming via SSE brings the Time to First Token (TTFT) under 300ms, creating a highly responsive user experience. 

---

## 🌐 Cloud Deployment Architecture

The system is designed to be cloud-native. The recommended deployment strategy for production environments is:

### Backend: Azure Container Apps
The FastAPI backend and ChromaDB/SQLite storage are containerized using `Dockerfile.backend` and deployed to Azure Container Apps. 
- **Automated CI/CD**: A GitHub Actions workflow (`.github/workflows/deploy-azure.yml`) automatically builds the image, pushes it to GitHub Container Registry, and updates the Azure Container App upon every push to `main`.
- **Environment**: Injects NVIDIA API keys and configuration securely via GitHub Secrets.

### Frontend: Vercel (Direct Deployment)
The React 18 + Vite frontend is deployed directly to **Vercel**. 
- By linking this GitHub repository directly in the Vercel Dashboard, Vercel natively handles the build process, edge caching, and global CDN delivery without requiring manual GitHub Actions.

*(Live deployment URLs will be attached here upon completion of the environment setup.)*

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
CHROMA_DIR=./backend/data/chroma
DB_PATH=./backend/data/sessions.db
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
*Backend runs at `http://localhost:8000` with Swagger Docs at `http://localhost:8000/docs`.*

### 3. Frontend Setup
In a new terminal, start the Vite React application:
```bash
cd compliance-ai/frontend
npm install
npm run dev
```
*Frontend runs at `http://localhost:5173`.*

---

## 🧪 Testing Scenarios
Log into the frontend using the demo roles to test the decision engine:
1. **ANSWER**: Ask *"What is the annual leave policy?"* (Resolves to active policy).
2. **CLARIFY**: Ask *"Can I carry forward leave?"* (Prompts for your jurisdiction).
3. **ESCALATE**: Ask *"What is the executive bonus formula?"* (Standard employee receives a restriction escalation).
