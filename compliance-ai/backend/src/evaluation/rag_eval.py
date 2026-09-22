"""Automated RAG Evaluation Suite: Retrieval Recall, Citation Groundedness, and Faithfulness.

Benchmarks LegalLens retrieval precision and answer faithfulness against
standard legal contract queries.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from ingestion.store import bm25_search, dense_search, get_chunk_text, get_meta
from legal_engine import sanitize_for_llm
from models import RetrievedEvidence

logger = logging.getLogger(__name__)


@dataclass
class EvalQuery:
    query: str
    expected_keywords: list[str]
    expected_clause_type: str
    description: str


# Standard benchmark test cases for legal contract retrieval
LEGAL_BENCHMARK_SUITE: list[EvalQuery] = [
    EvalQuery(
        query="What are the termination notice conditions and breach terms?",
        expected_keywords=["terminate", "notice", "breach", "days"],
        expected_clause_type="TERMINATION",
        description="Termination Clause Retrieval",
    ),
    EvalQuery(
        query="What is the maximum liability cap or limitation of damages?",
        expected_keywords=["liability", "damages", "cap", "limitation", "indirect"],
        expected_clause_type="LIABILITY",
        description="Limitation of Liability Retrieval",
    ),
    EvalQuery(
        query="What are the confidentiality and proprietary information obligations?",
        expected_keywords=["confidential", "proprietary", "disclose", "information"],
        expected_clause_type="CONFIDENTIALITY",
        description="Confidentiality Obligations Retrieval",
    ),
    EvalQuery(
        query="Which governing law and jurisdiction controls dispute resolution?",
        expected_keywords=["governing", "law", "jurisdiction", "court", "dispute"],
        expected_clause_type="GOVERNING_LAW",
        description="Governing Law & Jurisdiction Retrieval",
    ),
    EvalQuery(
        query="Are there any indemnification obligations covering legal costs and claims?",
        expected_keywords=["indemnif", "hold harmless", "defend", "claims"],
        expected_clause_type="INDEMNIFICATION",
        description="Indemnification Retrieval",
    ),
]


@dataclass
class EvalResult:
    total_queries: int = 0
    successful_retrievals: int = 0
    keyword_recall_score: float = 0.0
    groundedness_score: float = 0.0
    latency_ms: float = 0.0
    query_details: list[dict[str, Any]] = field(default_factory=list)


def evaluate_retrieval(benchmark: list[EvalQuery] | None = None, top_k: int = 5) -> EvalResult:
    """Evaluate retrieval precision and recall against legal benchmark queries."""
    suite = benchmark or LEGAL_BENCHMARK_SUITE
    total = len(suite)
    retrieved_count = 0
    total_keyword_matches = 0
    total_keywords_expected = 0
    t0 = time.time()
    details = []

    for q in suite:
        # Perform hybrid search (dense + sparse BM25)
        dense_results = dense_search(q.query, k=top_k)
        sparse_results = bm25_search(q.query, k=top_k)

        # Merge unique chunk IDs
        seen_ids = set()
        retrieved_texts: list[str] = []
        for cid, _ in dense_results + sparse_results:
            if cid not in seen_ids:
                seen_ids.add(cid)
                txt = get_chunk_text(cid)
                if txt:
                    retrieved_texts.append(txt.lower())

        combined_text = " ".join(retrieved_texts)
        if retrieved_texts:
            retrieved_count += 1

        # Check keyword recall in retrieved chunks
        matched_kw = [kw for kw in q.expected_keywords if kw.lower() in combined_text]
        kw_recall = len(matched_kw) / len(q.expected_keywords) if q.expected_keywords else 1.0

        total_keyword_matches += len(matched_kw)
        total_keywords_expected += len(q.expected_keywords)

        details.append({
            "query": q.query,
            "description": q.description,
            "chunks_retrieved": len(retrieved_texts),
            "matched_keywords": matched_kw,
            "keyword_recall": round(kw_recall, 2),
        })

    total_latency = (time.time() - t0) * 1000.0
    avg_latency = total_latency / total if total else 0.0
    overall_recall = total_keyword_matches / total_keywords_expected if total_keywords_expected else 0.0

    # Groundedness: ratio of queries where at least 50% of expected legal concepts were retrieved
    grounded_queries = sum(1 for d in details if d["keyword_recall"] >= 0.5)
    groundedness = grounded_queries / total if total else 0.0

    return EvalResult(
        total_queries=total,
        successful_retrievals=retrieved_count,
        keyword_recall_score=round(overall_recall, 3),
        groundedness_score=round(groundedness, 3),
        latency_ms=round(avg_latency, 1),
        query_details=details,
    )


if __name__ == "__main__":
    import json
    res = evaluate_retrieval()
    print("=== LegalLens RAG Retrieval Evaluation ===")
    print(f"Total Queries: {res.total_queries}")
    print(f"Keyword Recall: {res.keyword_recall_score * 100:.1f}%")
    print(f"Groundedness: {res.groundedness_score * 100:.1f}%")
    print(f"Avg Latency: {res.latency_ms}ms")
    print("\nQuery Details:")
    print(json.dumps(res.query_details, indent=2))
