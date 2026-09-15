"""Multi-format document parsing (PDF, DOCX, TXT, MD) to text + section headings."""
from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader
from docx import Document as DocxDocument

SUPPORTED_EXT = {".pdf", ".docx", ".txt", ".md", ".markdown"}


def parse(path: Path) -> list[tuple[str, str]]:
    """Parse a document into a list of (heading, paragraph_text) pairs."""
    ext = path.suffix.lower()
    if ext == ".pdf":
        return _parse_pdf(path)
    if ext == ".docx":
        return _parse_docx(path)
    if ext in {".txt", ".md", ".markdown"}:
        return _parse_text(path)
    raise ValueError(f"Unsupported file type: {ext}")


def parse_text(text: str, suffix: str = ".md") -> list[tuple[str, str]]:
    """Parse a text buffer (front-matter already stripped)."""
    if suffix.lower() not in {".txt", ".md", ".markdown"}:
        raise ValueError("parse_text only supports text/markdown")
    blocks: list[tuple[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if _looks_like_heading(line):
            blocks.append((line.strip("#").strip(), ""))
        else:
            blocks.append(("Body", line))
    return blocks


def _parse_pdf(path: Path) -> list[tuple[str, str]]:
    reader = PdfReader(str(path))
    blocks: list[tuple[str, str]] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        for raw in text.split("\n"):
            line = raw.strip()
            if not line:
                continue
            if _looks_like_heading(line):
                blocks.append((line, ""))
            else:
                blocks.append(("Body", line))
    return blocks


def _parse_docx(path: Path) -> list[tuple[str, str]]:
    doc = DocxDocument(str(path))
    blocks: list[tuple[str, str]] = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        style = (para.style.name or "").lower()
        if "heading" in style or "title" in style:
            blocks.append((text, ""))
        else:
            blocks.append(("Body", text))
    return blocks


def _parse_text(path: Path) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line:
            continue
        if _looks_like_heading(line):
            blocks.append((line.strip("#").strip(), ""))
        else:
            blocks.append(("Body", line))
    return blocks


def _looks_like_heading(line: str) -> bool:
    if line.startswith("#"):
        return True
    # uppercase short line heuristic
    stripped = line.lstrip("# ").strip()
    if 3 <= len(stripped) <= 60 and stripped.isupper() and not stripped.endswith("."):
        return True
    return False