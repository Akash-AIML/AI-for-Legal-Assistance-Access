"""Chunk parsed blocks into retrievable sections, keeping sections together."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from models import Chunk, DocMetadata


def build_chunks(
    source_path: str,
    blocks: list[tuple[str, str]],
    meta: DocMetadata,
    max_chars: int = 1600,
) -> list[Chunk]:
    """Group heading-delimited sections into chunks.

    - A heading starts a new section; body lines under it accumulate into a chunk.
    - Sections larger than max_chars are split on paragraph/word boundaries.
    - Unstructured blocks (heading "Body") are merged into rolling windows.
    """
    meta = meta.model_copy(deep=True)
    meta.source_path = source_path

    chunks: list[Chunk] = []
    buffer: list[str] = []
    section = ""
    index = 0

    def flush():
        nonlocal buffer, section, index
        text = "\n".join(buffer).strip()
        if not text:
            return
        # split oversized sections
        if len(text) > max_chars:
            for seg in _split_text(text, max_chars):
                chunks.append(_make_chunk(meta, source_path, section, index, seg))
                index += 1
        else:
            chunks.append(_make_chunk(meta, source_path, section, index, text))
            index += 1
        buffer = []

    for heading, line in blocks:
        if heading != "Body":
            flush()
            section = heading
        if line:
            buffer.append(line)
    flush()
    return chunks


def _make_chunk(meta: DocMetadata, source: str, section: str, index: int, text: str) -> Chunk:
    chunk_id = f"{meta.document_id}__{_slug(section or 'body')}__{index}"
    return Chunk(
        chunk_id=chunk_id,
        doc_id=meta.document_id,
        section=section or "Body",
        index=index,
        text=text,
        metadata=meta,
    )


def _split_text(text: str, max_chars: int) -> list[str]:
    parts, cur = [], ""
    for para in text.split("\n"):
        if len(cur) + len(para) + 1 <= max_chars:
            cur = f"{cur}\n{para}".strip()
        else:
            if cur:
                parts.append(cur)
            word_wrap = []
            for word in para.split(" "):
                if len(" ".join(word_wrap)) + len(word) + 1 > max_chars and word_wrap:
                    parts.append(" ".join(word_wrap))
                    word_wrap = []
                word_wrap.append(word)
            cur = " ".join(word_wrap)
    if cur:
        parts.append(cur)
    return parts


def _slug(s: str) -> str:
    keep = "".join(ch if ch.isalnum() else "_" for ch in s)
    return (keep[:32] or "body").strip("_")


def split_frontmatter(text: str) -> tuple[str, str]:
    """Split text into (front_matter, body). Returns ("", text) if no YAML block."""
    text = text.lstrip("\ufeff").lstrip("\n")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[1], parts[2].lstrip("\n")
    return "", text


def parse_meta_yaml(text: str) -> DocMetadata:
    """Parse a YAML-style front-matter block into DocMetadata.

    `text` is expected to be the inner content between the `---` delimiters.
    Falls back to defaults when nothing parses.
    """
    meta = DocMetadata()
    text = text.strip()
    for line in text.splitlines():
        line = line.strip()
        if ":" not in line or line.startswith("#"):
            continue
        key, _, val = line.partition(":")
        val = val.strip().strip('"').strip("'")
        if not val:
            continue
        key = key.strip()
        try:
            if key in {"effective_date", "review_date", "expiry_date"}:
                if val:
                    from datetime import date
                    setattr(meta, key, date.fromisoformat(val))
            elif key == "access_roles":
                meta.access_roles = [r.strip() for r in val.split(",") if r.strip()]
            elif key == "tags":
                meta.tags = [t.strip() for t in val.split(",") if t.strip()]
            elif key == "status":
                meta.status = meta.status.__class__(val.upper())
            elif key == "authority_type":
                from models import AuthorityType
                try:
                    meta.authority_type = AuthorityType(val.upper())
                except ValueError:
                    pass
            else:
                setattr(meta, key, val)
        except (ValueError, AttributeError):
            pass
    return meta