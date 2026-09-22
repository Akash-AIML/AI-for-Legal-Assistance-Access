"""Tests for RAG retrieval evaluation and benchmarking."""
from __future__ import annotations

import pytest
from evaluation.rag_eval import EvalQuery, evaluate_retrieval


def test_rag_evaluation_runs_and_computes_metrics():
    """RAG benchmark evaluates queries and returns valid metrics."""
    test_suite = [
        EvalQuery(
            query="termination notice and breach",
            expected_keywords=["terminate", "notice"],
            expected_clause_type="TERMINATION",
            description="Termination Test Query",
        ),
    ]

    res = evaluate_retrieval(benchmark=test_suite, top_k=3)
    assert res.total_queries == 1
    assert res.latency_ms >= 0
    assert 0.0 <= res.keyword_recall_score <= 1.0
    assert 0.0 <= res.groundedness_score <= 1.0
    assert len(res.query_details) == 1
    assert "query" in res.query_details[0]
    assert "keyword_recall" in res.query_details[0]
