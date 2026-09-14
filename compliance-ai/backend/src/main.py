"""FastAPI application entry point."""
from __future__ import annotations

import threading
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api import auth_routes, chat_routes, document_routes, escalation_routes, legal_routes, speech_routes, tts_routes
from auth import get_current_user
from config import get_settings
from ingestion import store
from memory import store as memory

tags_metadata = [
    {
        "name": "Authentication",
        "description": "JWT authentication, user identity validation, and role profile retrieval.",
    },
    {
        "name": "Legal Document Analysis",
        "description": "Document X-Ray analysis, clause classification, risk assessment, and obligation extraction.",
    },
    {
        "name": "Document Comparison",
        "description": "Clause-level semantic comparison between two legal documents with impact analysis.",
    },
    {
        "name": "Lawyer Brief",
        "description": "Generate structured pre-consultation briefs for legal professionals.",
    },
    {
        "name": "Knowledge Retrieval & Decisions",
        "description": "LangGraph query processing with evidence assessment (ANSWER, CLARIFY, ESCALATE).",
    },
    {
        "name": "Policy Documents & Governance",
        "description": "Document upload, status management, and ChromaDB vector chunk indexing.",
    },
    {
        "name": "Escalation Governance",
        "description": "Human-in-the-loop escalation ticket management and resolution workflows.",
    },
]

app = FastAPI(
    title="LegalLens — AI Legal Document Intelligence API",
    version="2.0.0",
    description="""
# LegalLens API Documentation

Evidence-first AI for understanding legal documents. LegalLens analyzes contracts, agreements, and legal notices to identify risks, extract obligations, and help users prepare for legal consultations.

### Key Capabilities:
- **Document X-Ray**: Upload a legal document and receive structured risk findings, clause classifications, obligation extraction, and lawyer preparation questions.
- **Contract Comparison**: Compare two documents clause-by-clause with plain-English impact analysis.
- **Lawyer Brief Generation**: Produce structured pre-consultation briefs with recommended questions.
- **Legal Q&A**: Ask questions about indexed documents and receive grounded, cited answers.
- **Evidence Assessment**: 6-dimension evidence evaluation with version/authority resolution.
- **LangGraph Decision Routing**: ANSWER, CLARIFY, RETRIEVE MORE, or ESCALATE based on evidence quality.

### Safety
Uploaded documents are treated as untrusted data. Document content is isolated from system instructions to prevent prompt injection.
    """,
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(chat_routes.router)
app.include_router(document_routes.router)
app.include_router(escalation_routes.router)
app.include_router(legal_routes.router)
app.include_router(speech_routes.router)
app.include_router(tts_routes.router)

_settings = get_settings()


@app.on_event("startup")
def startup():
    # Asynchronously initialize vector index in background thread to prevent Azure Web App 503 health probe timeouts
    threading.Thread(target=store.rebuild_index, daemon=True).start()


@app.get("/api/health", tags=["System & Audit"])
def health():
    return {
        "status": "ok",
        "chunks": store.count_chunks(),
        "documents": len(store.list_documents()),
        "offline_mode": _settings.llm_offline,
    }


@app.get("/api/audit/recent", tags=["System & Audit"])
def audit_recent(user: dict = Depends(get_current_user)):
    if user["role"] not in ("Admin", "Compliance", "HR"):
        from fastapi import HTTPException

        raise HTTPException(403, "Insufficient permissions")
    return {"turns": memory.recent_audit(50)}


# Serve frontend build if present
_frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")