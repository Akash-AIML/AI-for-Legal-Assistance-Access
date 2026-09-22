"""ChromaDB vector store repository and document persistence.

Manages collection lifecycle, chunk upsertion, document deletion, and re-exports
retrieval and search operations from `ingestion.search`.
"""
from __future__ import annotations

import logging
import threading

import chromadb

from config import get_settings
from llm import embed_texts
from models import Chunk

from ingestion.search import (
    FEATURED_DEMO_DOC_IDS,
    append_to_bm25,
    bm25_search,
    count_chunks,
    dense_search,
    get_chunk_text,
    get_chunks_for_doc,
    get_meta,
    hybrid_search,
    list_documents,
    rebuild_index,
    _ensure_index,
    _meta_index,
    _bm25_ids,
    _bm25_corpus,
)

logger = logging.getLogger(__name__)
_settings = get_settings()
_client = None
_client_lock = threading.Lock()


def get_collection():
    """Thread-safe acquisition of ChromaDB collection with Ephemeral fallback."""
    global _client
    with _client_lock:
        if _client is None:
            try:
                _client = chromadb.PersistentClient(path=_settings.chroma_dir)
            except Exception as exc:
                logger.warning(
                    "Failed to initialize PersistentClient at %s (%s). Falling back to EphemeralClient.",
                    _settings.chroma_dir,
                    exc,
                )
                _client = chromadb.EphemeralClient()
        return _client.get_or_create_collection(
            _settings.collection_name,
            metadata={"hnsw:space": "cosine"},
        )


def _flat_meta(chunk: Chunk) -> dict:
    """Flatten Chunk metadata into scalar attributes for ChromaDB."""
    m = chunk.metadata
    return {
        "chunk_id": chunk.chunk_id,
        "document_id": m.document_id,
        "title": m.title,
        "document_type": m.document_type,
        "department": m.department,
        "jurisdiction": m.jurisdiction,
        "version": m.version,
        "index": chunk.index,
        "effective_date": m.effective_date.isoformat() if m.effective_date else "",
        "review_date": m.review_date.isoformat() if m.review_date else "",
        "expiry_date": m.expiry_date.isoformat() if m.expiry_date else "",
        "status": m.status.value if hasattr(m.status, "value") else str(m.status),
        "authority": m.authority,
        "authority_type": m.authority_type.value if hasattr(m, "authority_type") and hasattr(m.authority_type, "value") else str(getattr(m, "authority_type", "USER_DOCUMENT")),
        "governing_law": getattr(m, "governing_law", ""),
        "country": getattr(m, "country", ""),
        "state": getattr(m, "state", ""),
        "citation": getattr(m, "citation", ""),
        "source_path": m.source_path,
        "owner": getattr(m, "owner", "global") or "global",
        "access_roles": ",".join(m.access_roles),
        "tags": ",".join(m.tags),
        "section": chunk.section,
    }


def upsert_chunks(chunks: list[Chunk]) -> int:
    """Embed and store chunks in ChromaDB and update BM25 index incrementally."""
    if not chunks:
        return 0
    col = get_collection()
    embs = embed_texts([c.text for c in chunks], input_type="passage")
    try:
        col.upsert(
            ids=[c.chunk_id for c in chunks],
            embeddings=embs,
            documents=[c.text for c in chunks],
            metadatas=[_flat_meta(c) for c in chunks],
        )
    except Exception as exc:
        if "dimension" in str(exc).lower():
            logger.warning("Chroma collection dimension mismatch, recreating collection: %s", exc)
            with _client_lock:
                _client.delete_collection(_settings.collection_name)
                col = _client.get_or_create_collection(
                    _settings.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
            col.upsert(
                ids=[c.chunk_id for c in chunks],
                embeddings=embs,
                documents=[c.text for c in chunks],
                metadatas=[_flat_meta(c) for c in chunks],
            )
        else:
            raise
    append_to_bm25(chunks)
    return len(chunks)


def delete_document(document_id: str) -> int:
    """Delete all chunks for a document from vector store and rebuild in-memory index."""
    col = get_collection()
    ids = [cid for cid, m in _meta_index.items() if m.get("document_id") == document_id]
    if ids:
        col.delete(ids=ids)
        rebuild_index()
    return len(ids)


def count_raw() -> int:
    """Count raw chunk records in ChromaDB collection."""
    try:
        return get_collection().count()
    except Exception:
        return 0


__all__ = [
    "get_collection",
    "upsert_chunks",
    "delete_document",
    "count_raw",
    "count_chunks",
    "rebuild_index",
    "append_to_bm25",
    "bm25_search",
    "dense_search",
    "hybrid_search",
    "get_chunk_text",
    "get_meta",
    "get_chunks_for_doc",
    "list_documents",
    "FEATURED_DEMO_DOC_IDS",
]