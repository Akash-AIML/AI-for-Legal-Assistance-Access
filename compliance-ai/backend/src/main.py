"""FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager
import threading
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel

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

import os

_is_serverless = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Asynchronously initialize vector index in background thread only in persistent environments
    if not _is_serverless:
        threading.Thread(target=store.rebuild_index, daemon=True).start()
    yield


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
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=None if _is_serverless else lifespan,
)

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        accept = request.headers.get("accept", "")
        if "text/markdown" in accept.lower():
            path = request.url.path
            if path == "/" or path == "/index.md":
                content = "# LegalLens AI\n\nLegalLens AI is an Enterprise Compliance & Operations Assistant that uses a LangGraph-driven Evidence Decision Engine to actively resolve outdated, conflicting, or unauthorized information.\n\n## Key Features\n- **Structure-Aware Chunking:** Parses logical document boundaries.\n- **RBAC Meta-filtering:** Database-level role-based access control.\n- **Pre-LLM Precedence:** Resolves version and date conflicts before they hit the LLM.\n- **Hybrid RRF Search:** Combines dense semantic and sparse BM25 search.\n- **LangGraph State Machine:** Bounds LLM responses to prevent hallucination.\n\nFor documentation, see our [llms.txt](/llms.txt)."
                return Response(content=content, status_code=200, media_type="text/markdown", headers={"Vary": "Accept"})
            else:
                content = "# 404 Not Found\n\nThe requested resource could not be found.\n\nIf you are an AI agent looking for documentation or capabilities, please refer to:\n- [llms.txt](/llms.txt) for agentic usage instructions.\n- [Sitemap](/sitemap.xml) for a full list of indexable pages.\n- [MCP](/.well-known/mcp) for our Model Context Protocol definitions."
                return Response(content=content, status_code=404, media_type="text/markdown", headers={"Vary": "Accept"})
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY"},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ai-for-legal-assistance-access-pi.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
    ],
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
@app.middleware("http")
async def add_rest_headers(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception as exc:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error_message": str(exc),
                "error_type": type(exc).__name__,
                "traceback": traceback.format_exc().splitlines(),
                "path": request.url.path,
            },
            headers={
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Referrer-Policy": "strict-origin-when-cross-origin",
            },
        )
    # REST headers
    response.headers["X-RateLimit-Limit"] = "100"
    response.headers["X-RateLimit-Remaining"] = "99"
    response.headers["X-RateLimit-Reset"] = "3600"
    response.headers["API-Version"] = "v1"
    response.headers["Deprecation"] = "false"
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"
    return response

app.include_router(auth_routes.router)
app.include_router(chat_routes.router)
app.include_router(document_routes.router)
app.include_router(escalation_routes.router)
app.include_router(legal_routes.router)
app.include_router(speech_routes.router)
app.include_router(tts_routes.router)

_settings = get_settings()




class HealthResponse(BaseModel):
    status: str
    chunks: int
    documents: int
    offline_mode: bool

@app.get("/api/health", tags=["System & Audit"], operation_id="get_health_status", response_model=HealthResponse, description="Returns the current system health status, including vector index chunk counts and offline mode configuration.")
def health():
    return {
        "status": "ok",
        "chunks": store.count_chunks(),
        "documents": len(store.list_documents()),
        "offline_mode": _settings.llm_offline,
    }


@app.get("/api/audit/recent", tags=["System & Audit"], operation_id="get_recent_audit_logs", description="Retrieves the 50 most recent audit logs for LangGraph evidence decisions. Requires Admin, Compliance, or HR role.")
def audit_recent(user: dict = Depends(get_current_user)):
    if user["role"] not in ("Admin", "Compliance", "HR"):
        from fastapi import HTTPException

        raise HTTPException(403, "Insufficient permissions")
    return {"turns": memory.recent_audit(50)}


# Serve frontend build if present
_frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")