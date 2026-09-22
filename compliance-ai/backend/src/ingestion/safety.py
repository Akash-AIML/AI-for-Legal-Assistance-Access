"""Document content sanitization and prompt injection defense.

Uploaded documents are untrusted data. This module ensures document content
is treated as evidence, never as executable instructions.
"""
from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

UNTRUSTED_MARKER = "<untrusted_document_content>"
UNTRUSTED_END_MARKER = "</untrusted_document_content>"

# Patterns that suggest prompt injection attempts in document text
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?prior\s+instructions",
    r"disregard\s+(all\s+)?previous",
    r"you\s+are\s+now\s+a",
    r"system\s*prompt",
    r"reveal\s+(your|the)\s+(system|instructions)",
    r"act\s+as\s+if",
    r"pretend\s+you\s+are",
    r"override\s+(your|the)\s+(instructions|rules)",
    r"forget\s+(all|your)\s+(previous|prior|instructions)",
    r"new\s+instructions:",
    r"important\s+new\s+instructions",
]

_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)


def wrap_untrusted(content: str) -> str:
    """Wrap document content in structural delimiters for prompt isolation.

    This ensures the LLM treats the content as data to analyze,
    not as instructions to follow.

    >>> wrap_untrusted("Some contract text")
    '<untrusted_document_content>\\nSome contract text\\n</untrusted_document_content>'
    """
    return f"{UNTRUSTED_MARKER}\n{content}\n{UNTRUSTED_END_MARKER}"


def detect_injection(text: str) -> list[str]:
    """Scan document text for potential prompt injection patterns.

    Returns a list of matched patterns (for logging/testing).
    Does NOT block the document — just flags it.
    """
    return _INJECTION_RE.findall(text)


def sanitize_for_llm(content: str) -> str:
    """Full sanitization pipeline: wrap + detect (for logging).

    Returns the wrapped content ready for LLM consumption.
    Injection attempts are logged but do not block processing.
    """
    matches = detect_injection(content)
    if matches:
        logger.warning("Potential injection patterns detected: %s", matches)
    return wrap_untrusted(content)
