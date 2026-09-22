"""High-level ingestion: file -> chunks -> ChromaDB + BM25."""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

from ingestion import store
from ingestion.chunker import build_chunks, parse_meta_yaml, split_frontmatter
from ingestion.parser import parse, parse_text
from models import DocMetadata


def ingest_file(path: Path, override: DocMetadata | None = None, owner: str | None = None) -> int:
    """Parse, chunk, and index a single document. Returns number of chunks added."""
    ext = path.suffix.lower()

    if ext in {".pdf", ".docx"}:
        # Binary files: use structured parser directly, do not call read_text
        blocks = parse(path)
        meta = override if override is not None else DocMetadata()
    else:
        # Text/Markdown files: parse YAML frontmatter if present
        raw = path.read_text(encoding="utf-8", errors="ignore")
        meta = override if override is not None else parse_meta_yaml(split_frontmatter(raw)[0])
        _, body = split_frontmatter(raw)
        blocks = parse_text(body, ext)

    if not meta.document_id:
        meta.document_id = _default_doc_id(path, meta)
    if not meta.title:
        meta.title = _readable_title(path)
    if not meta.source_path:
        meta.source_path = str(path)
    if owner:
        meta.owner = owner
    if "uploads" in str(path).lower():
        meta.authority_type = "USER_DOCUMENT"

    chunks = build_chunks(str(path), blocks, meta)
    return store.upsert_chunks(chunks)



def _default_doc_id(path: Path, meta: DocMetadata) -> str:
    import re
    clean_stem = re.sub(r'[^a-zA-Z0-9]', '_', path.stem).strip('_').upper()
    return f"{clean_stem}"


def _readable_title(path: Path) -> str:
    """Derive a human-readable title from the filename when the doc has no front-matter."""
    return path.stem.replace("_", " ").replace("-", " ").strip()


def ingest_directory(directory: Path) -> dict[str, int]:
    """Ingest every supported file in a directory. Returns {filename: chunks}."""
    from ingestion.parser import SUPPORTED_EXT

    results: dict[str, int] = {}
    for p in sorted(directory.iterdir()):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXT:
            try:
                results[p.name] = ingest_file(p)
            except Exception as exc:  # keep going on per-file failures
                results[p.name] = 0
                logger.error("Failed to ingest %s: %s", p.name, exc)
    return results