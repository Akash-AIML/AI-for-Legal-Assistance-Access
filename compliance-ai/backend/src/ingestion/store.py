"""ChromaDB vector store + in-memory BM25 index.

Chunks carry flat metadata (scalars) driving permission-aware filtering and
freshness checks. Hybrid retrieval fuses dense + BM25 by Reciprocal Rank Fusion.
"""
from __future__ import annotations

import logging
from pathlib import Path
import threading
from typing import Optional

logger = logging.getLogger(__name__)
import chromadb
from rank_bm25 import BM25Okapi

from config import get_settings
from llm import embed_texts
from models import Chunk, role_privileges

_settings = get_settings()
_client = None
_client_lock = threading.Lock()

# chunk_id -> flat metadata map, kept in sync after every write/rebuild
_meta_index: dict[str, dict] = {}
_bm25_corpus: list[str] = []
_bm25_ids: list[str] = []
_bm25: Optional[BM25Okapi] = None


def get_collection():
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
        "status": m.status.value if hasattr(m.status, 'value') else str(m.status),
        "authority": m.authority,
        "authority_type": m.authority_type.value if hasattr(m, 'authority_type') and hasattr(m.authority_type, 'value') else str(getattr(m, 'authority_type', 'USER_DOCUMENT')),
        "governing_law": getattr(m, 'governing_law', ''),
        "country": getattr(m, 'country', ''),
        "state": getattr(m, 'state', ''),
        "citation": getattr(m, 'citation', ''),
        "source_path": m.source_path,
        "owner": getattr(m, 'owner', 'global') or 'global',
        "access_roles": ",".join(m.access_roles),
        "tags": ",".join(m.tags),
        "section": chunk.section,
    }


def upsert_chunks(chunks: list[Chunk]) -> int:
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


def append_to_bm25(new_chunks: list[Chunk]) -> None:
    """Incrementally update BM25 corpus and metadata index with new chunks (avoiding full collection scans)."""
    global _bm25, _bm25_corpus, _bm25_ids, _meta_index
    if not new_chunks:
        return
    if _bm25 is None:
        rebuild_index()
        return

    for c in new_chunks:
        _bm25_ids.append(c.chunk_id)
        _bm25_corpus.append(c.text)
        _meta_index[c.chunk_id] = _flat_meta(c)

    tokenized = [t.split() for t in _bm25_corpus]
    _bm25 = BM25Okapi(tokenized) if tokenized else None


def rebuild_index() -> None:
    """Re-read all chunks (text + metadata) and rebuild BM25 + meta indexes."""
    global _bm25, _bm25_corpus, _bm25_ids, _meta_index
    try:
        col = get_collection()
        data = col.get(include=["documents", "metadatas"])
        _bm25_corpus = data.get("documents", []) or []
        _bm25_ids = data.get("ids", []) or []
        metas = data.get("metadatas", []) or []
        _meta_index = {cid: m for cid, m in zip(_bm25_ids, metas) if m}
        tokenized = [t.split() for t in _bm25_corpus]
        _bm25 = BM25Okapi(tokenized) if tokenized else None
    except Exception as exc:
        logger.warning("rebuild_index encountered error: %s", exc)


def _ensure_index() -> None:
    """Lazily rebuild the index on first use in a fresh process."""
    if _bm25 is None and count_raw() > 0:
        rebuild_index()


def count_raw() -> int:
    try:
        return get_collection().count()
    except Exception:
        return 0


def bm25_search(query: str, k: int = _settings.bm25_k) -> list[tuple[str, float]]:
    _ensure_index()
    if _bm25 is None or not query.strip():
        return []
    scores = _bm25.get_scores(query.split())
    ranked = sorted(zip(_bm25_ids, scores), key=lambda t: -t[1])
    return [(cid, s) for cid, s in ranked[:k] if s > 0]


def _roles_ok(meta: Optional[dict], allowed_roles: Optional[list[str]]) -> bool:
    """Permission check: chunk's access_roles must intersect the user's privileges.

    Roles are hierarchical (see models.role_privileges), so e.g. Admin inherits
    access to Employee and Compliance content.
    """
    if not allowed_roles:
        return True
    if not meta:
        return False
    chunk_roles = [r.strip() for r in (meta.get("access_roles", "") or "").split(",") if r.strip()]
    if not chunk_roles:
        return True
    return bool(set(chunk_roles) & role_privileges(allowed_roles))


def _filter_roles(
    results: list[tuple[str, float]], allowed_roles: Optional[list[str]]
) -> list[tuple[str, float]]:
    if not allowed_roles:
        return results
    return [(cid, s) for cid, s in results if _roles_ok(_meta_index.get(cid), allowed_roles)]


import functools
import time

@functools.lru_cache(maxsize=256)
def _get_query_embedding(query: str) -> list[float]:
    """Cached query embedding to avoid redundant network calls for identical queries."""
    return embed_texts([query], input_type="query")[0]


def dense_search(
    query: str,
    k: int = _settings.dense_k,
    allowed_roles: Optional[list[str]] = None,
    where: Optional[dict] = None,
) -> list[tuple[str, float]]:
    """Dense search returning (chunk_id, sim). Permission filter applied in Python."""
    _ensure_index()
    t0 = time.time()
    col = get_collection()
    if not query.strip():
        return []
    q = _get_query_embedding(query)
    res = col.query(query_embeddings=[q], n_results=k, where=where or None)
    out = [(cid, 1.0 - dist) for cid, dist in zip(res["ids"][0], res["distances"][0])]
    filtered = _filter_roles(out, allowed_roles)
    dt = (time.time() - t0) * 1000.0
    logger.debug("Dense search for '%s' took %.1fms | raw=%d -> filtered=%d", query[:30], dt, len(out), len(filtered))
    return filtered


def hybrid_search(
    query: str,
    allowed_roles: Optional[list[str]] = None,
) -> list[tuple[str, float]]:
    """Dense + BM25 fused by Reciprocal Rank Fusion -> (chunk_id, score)."""
    t0 = time.time()
    _ensure_index()
    dense = dense_search(query, _settings.dense_k, allowed_roles)
    
    t_bm25 = time.time()
    bm25 = _filter_roles(bm25_search(query, _settings.bm25_k), allowed_roles)
    dt_bm25 = (time.time() - t_bm25) * 1000.0
    logger.debug("BM25 search took %.1fms | hits=%d", dt_bm25, len(bm25))

    k = 60
    scores: dict[str, float] = {}
    for rank, (cid, _) in enumerate(dense):
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
    for rank, (cid, _) in enumerate(bm25):
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
    if not scores:
        scores = {cid: 0.0 for cid, _ in dense}
    ranked = sorted(scores.items(), key=lambda t: -t[1])
    dt_total = (time.time() - t0) * 1000.0
    logger.debug("Hybrid Search total %.1fms | results=%d", dt_total, len(ranked))
    return ranked[: _settings.final_k]


def get_chunk_text(chunk_id: str) -> Optional[str]:
    if _bm25_ids:
        idx = _bm25_ids.index(chunk_id) if chunk_id in _bm25_ids else -1
        if idx != -1:
            return _bm25_corpus[idx]
    col = get_collection()
    g = col.get(ids=[chunk_id], include=["documents"])
    return g["documents"][0] if g["ids"] else None


def get_meta(chunk_id: str) -> Optional[dict]:
    _ensure_index()
    return _meta_index.get(chunk_id)


def get_chunks_for_doc(doc_id: str) -> list[tuple[str, dict, str]]:
    """Public repository method returning all (chunk_id, metadata_dict, chunk_text) for a document.

    Eliminates external direct access to private _meta_index.
    """
    _ensure_index()
    chunks: list[tuple[str, dict, str]] = []
    for cid, meta in _meta_index.items():
        if not meta:
            continue
        c_doc_id = meta.get("document_id", "")
        source_path = meta.get("source_path", "")
        if (
            c_doc_id == doc_id
            or doc_id.lower() in source_path.lower()
            or Path(source_path).name.lower() == doc_id.lower()
        ):
            text = get_chunk_text(cid) or ""
            chunks.append((cid, meta, text))
    return chunks


FEATURED_DEMO_DOC_IDS = {
    "COMMERCIAL_REAL_ESTATE_LEASE_AGREEMENT_1",
    "SAAS_ENTERPRISE_SERVICE_AGREEMENT_2026",
    "GDPR_DATA_PROCESSING_ADDENDUM_DPA_1",
    "EMP-AGR-001",
    "REN-AGR-001",
}


def list_documents(owner: Optional[str] = None) -> list[dict]:
    """Summarize indexed documents (filtered by featured demo docs + user owner)."""
    _ensure_index()
    docs: dict[str, dict] = {}
    for meta in _meta_index.values():
        doc_id = meta["document_id"]
        doc_owner = meta.get("owner", "global") or "global"

        is_demo = doc_id in FEATURED_DEMO_DOC_IDS
        is_my_doc = bool(owner and (doc_owner.lower() == owner.lower()))

        # Show featured demo docs to everyone; show uploaded docs ONLY to the owner who uploaded them.
        if not (is_demo or is_my_doc or owner is None):
            continue

        doc = docs.setdefault(
            doc_id,
            {
                "document_id": doc_id,
                "title": meta["title"],
                "document_type": meta["document_type"],
                "department": meta["department"],
                "jurisdiction": meta["jurisdiction"],
                "version": meta["version"],
                "status": meta["status"],
                "effective_date": meta["effective_date"],
                "governing_law": meta.get("governing_law", ""),
                "country": meta.get("country", ""),
                "chunks": 0,
                "access_roles": meta["access_roles"],
                "source_path": meta.get("source_path", ""),
                "authority_type": meta.get("authority_type", "USER_DOCUMENT" if not is_demo else "CONTRACT"),
                "owner": doc_owner,
            },
        )
        doc["chunks"] += 1
    return sorted(docs.values(), key=lambda d: d["document_id"])


def delete_document(document_id: str) -> int:
    col = get_collection()
    ids = [cid for cid, m in _meta_index.items() if m.get("document_id") == document_id]
    if ids:
        col.delete(ids=ids)
        rebuild_index()
    return len(ids)


def count_chunks() -> int:
    _ensure_index()
    return len(_bm25_ids) or 0