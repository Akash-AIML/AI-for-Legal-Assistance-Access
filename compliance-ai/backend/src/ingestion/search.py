"""In-memory BM25 index, hybrid search (Reciprocal Rank Fusion), and metadata retrieval.

Provides dense semantic + sparse BM25 search with role-based access filtering
and cached query embeddings.
"""
from __future__ import annotations

import functools
import logging
from pathlib import Path
import time
from typing import Optional

from rank_bm25 import BM25Okapi

from config import get_settings
from llm import embed_texts
from models import Chunk, role_privileges

logger = logging.getLogger(__name__)
_settings = get_settings()

# chunk_id -> flat metadata map, kept in sync after every write/rebuild
_meta_index: dict[str, dict] = {}
_bm25_corpus: list[str] = []
_bm25_ids: list[str] = []
_bm25_tokenized: list[list[str]] = []
_bm25: Optional[BM25Okapi] = None

FEATURED_DEMO_DOC_IDS = {
    "COMMERCIAL_REAL_ESTATE_LEASE_AGREEMENT_1",
    "SAAS_ENTERPRISE_SERVICE_AGREEMENT_2026",
    "GDPR_DATA_PROCESSING_ADDENDUM_DPA_1",
    "EMP-AGR-001",
    "REN-AGR-001",
}


def _get_collection():
    """Lazy import to eliminate circular dependency with store.py."""
    from ingestion.store import get_collection
    return get_collection()


def rebuild_index() -> None:
    """Re-read all chunks (text + metadata) from vector store and rebuild BM25 + meta indexes."""
    global _bm25, _bm25_corpus, _bm25_ids, _meta_index, _bm25_tokenized
    try:
        col = _get_collection()
        data = col.get(include=["documents", "metadatas"])
        _bm25_corpus = data.get("documents", []) or []
        _bm25_ids = data.get("ids", []) or []
        metas = data.get("metadatas", []) or []
        _meta_index = {cid: m for cid, m in zip(_bm25_ids, metas) if m}
        _bm25_tokenized = [t.split() for t in _bm25_corpus]
        _bm25 = BM25Okapi(_bm25_tokenized) if _bm25_tokenized else None
    except Exception as exc:
        logger.warning("rebuild_index encountered error: %s", exc)


def append_to_bm25(new_chunks: list[Chunk]) -> None:
    """Incrementally update BM25 corpus and metadata index with new chunks in O(Delta N) time."""
    global _bm25, _bm25_corpus, _bm25_ids, _meta_index, _bm25_tokenized
    if not new_chunks:
        return
    if _bm25 is None or not _bm25_tokenized:
        rebuild_index()
        return

    from ingestion.store import _flat_meta
    new_tokenized: list[list[str]] = []
    for c in new_chunks:
        _bm25_ids.append(c.chunk_id)
        _bm25_corpus.append(c.text)
        _meta_index[c.chunk_id] = _flat_meta(c)
        new_tokenized.append(c.text.split())

    _bm25_tokenized.extend(new_tokenized)
    _bm25 = BM25Okapi(_bm25_tokenized) if _bm25_tokenized else None


def _ensure_index() -> None:
    """Lazily rebuild the index on first use in a fresh process."""
    if _bm25 is None:
        try:
            if _get_collection().count() > 0:
                rebuild_index()
        except Exception:
            pass


def _roles_ok(meta: Optional[dict], allowed_roles: Optional[list[str]]) -> bool:
    """Permission check: chunk's access_roles must intersect the user's privileges.

    Roles are hierarchical (see models.role_privileges).
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


@functools.lru_cache(maxsize=256)
def _get_query_embedding(query: str) -> list[float]:
    """Cached query embedding to avoid redundant network calls for identical queries."""
    return embed_texts([query], input_type="query")[0]


def bm25_search(query: str, k: int = _settings.bm25_k) -> list[tuple[str, float]]:
    """Sparse keyword search via BM25Okapi."""
    _ensure_index()
    if _bm25 is None or not query.strip():
        return []
    scores = _bm25.get_scores(query.split())
    ranked = sorted(zip(_bm25_ids, scores), key=lambda t: -t[1])
    return [(cid, s) for cid, s in ranked[:k] if s > 0]


def dense_search(
    query: str,
    k: int = _settings.dense_k,
    allowed_roles: Optional[list[str]] = None,
    where: Optional[dict] = None,
) -> list[tuple[str, float]]:
    """Dense semantic search returning (chunk_id, sim). Permission filter applied in Python."""
    _ensure_index()
    t0 = time.time()
    col = _get_collection()
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
    """Retrieve chunk document text by chunk_id."""
    if _bm25_ids:
        idx = _bm25_ids.index(chunk_id) if chunk_id in _bm25_ids else -1
        if idx != -1:
            return _bm25_corpus[idx]
    col = _get_collection()
    g = col.get(ids=[chunk_id], include=["documents"])
    return g["documents"][0] if g["ids"] else None


def get_meta(chunk_id: str) -> Optional[dict]:
    """Retrieve metadata dictionary for a given chunk_id."""
    _ensure_index()
    return _meta_index.get(chunk_id)


def get_chunks_for_doc(doc_id: str) -> list[tuple[str, dict, str]]:
    """Return all (chunk_id, metadata_dict, chunk_text) for a document."""
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


def count_chunks() -> int:
    """Total number of indexed chunks."""
    _ensure_index()
    return len(_bm25_ids) or 0
