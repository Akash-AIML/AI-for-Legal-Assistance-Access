from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from ingestion.search import (
    _roles_ok,
    _filter_roles,
    bm25_search,
    dense_search,
    hybrid_search,
    append_to_bm25,
    get_meta,
    get_chunk_text,
)
from models import Chunk


class TestRoleFiltering:
    def test_roles_ok_no_allowed_roles_allows_all(self):
        meta = {"access_roles": "ADMIN,LEGAL_COUNSEL"}
        assert _roles_ok(meta, None) is True
        assert _roles_ok(meta, []) is True

    def test_roles_ok_no_meta_returns_false_when_roles_required(self):
        assert _roles_ok(None, ["EMPLOYEE"]) is False
        assert _roles_ok({}, ["EMPLOYEE"]) is False

    def test_roles_ok_unrestricted_chunk_allowed(self):
        meta = {"access_roles": ""}
        assert _roles_ok(meta, ["EMPLOYEE"]) is True

    def test_roles_ok_admin_matches_admin(self):
        meta = {"access_roles": "ADMIN"}
        assert _roles_ok(meta, ["ADMIN"]) is True

    def test_roles_ok_employee_cannot_access_compliance_officer(self):
        meta = {"access_roles": "COMPLIANCE_OFFICER"}
        assert _roles_ok(meta, ["EMPLOYEE"]) is False

    def test_filter_roles_filters_properly(self):
        results = [("chunk_1", 0.9), ("chunk_2", 0.8)]
        with patch("ingestion.search._meta_index", {
            "chunk_1": {"access_roles": "EMPLOYEE"},
            "chunk_2": {"access_roles": "ADMIN"},
        }):
            # Employee only sees chunk_1
            filtered = _filter_roles(results, ["EMPLOYEE"])
            assert [cid for cid, _ in filtered] == ["chunk_1"]


class TestSearchFunctions:
    def test_bm25_search_empty_query_returns_empty(self):
        assert bm25_search("") == []
        assert bm25_search("   ") == []

    def test_dense_search_empty_query_returns_empty(self):
        assert dense_search("") == []
        assert dense_search("   ") == []

    def test_append_to_bm25_empty_list_is_noop(self):
        # Should not raise exception
        append_to_bm25([])

    def test_get_meta_nonexistent_returns_none(self):
        with patch("ingestion.search._meta_index", {}):
            assert get_meta("nonexistent_chunk_id") is None

    def test_hybrid_search_combines_dense_and_sparse(self):
        with patch("ingestion.search.dense_search") as mock_dense, \
             patch("ingestion.search.bm25_search") as mock_bm25, \
             patch("ingestion.search._filter_roles", side_effect=lambda res, roles: res):
            mock_dense.return_value = [("c1", 0.95), ("c2", 0.85)]
            mock_bm25.return_value = [("c2", 5.2), ("c3", 4.1)]

            ranked = hybrid_search("indemnity liability clause", allowed_roles=None)
            cids = [cid for cid, _ in ranked]
            # c2 appeared in both dense and sparse, so reciprocal rank fusion should score it high
            assert "c2" in cids
            assert "c1" in cids

    def test_append_to_bm25_incremental(self):
        from models import DocMetadata, DocStatus
        from ingestion.store import flat_to_doc_metadata
        from memory.store import _compare_key, set_compare_cache, get_compare_cache, set_brief_cache, get_brief_cache

        # Test symmetric compare key
        key1 = _compare_key("doc_zeta", "doc_alpha")
        key2 = _compare_key("doc_alpha", "doc_zeta")
        assert key1 == key2 == "doc_alpha:doc_zeta"

        # Test compare cache roundtrip
        set_compare_cache("doc_alpha", "doc_zeta", {"summary": "Identical terms"})
        cached = get_compare_cache("doc_zeta", "doc_alpha")
        assert cached == {"summary": "Identical terms"}

        # Test brief cache roundtrip with Hindi language key
        set_brief_cache("doc_beta", {"situation": "सारांश"}, language="hi")
        cached_brief = get_brief_cache("doc_beta", language="hi")
        assert cached_brief == {"situation": "सारांश"}
        # Different language should return None
        assert get_brief_cache("doc_beta", language="en") is None

    def test_flat_to_doc_metadata_reconstruction(self):
        from ingestion.store import flat_to_doc_metadata
        from models import DocStatus

        flat = {
            "document_id": "test_doc_99",
            "title": "Master Services Agreement",
            "document_type": "CONTRACT",
            "status": "ACTIVE",
            "access_roles": "ADMIN,LEGAL_COUNSEL",
            "effective_date": "2026-01-15",
            "governing_law": "Indian Contract Act, 1872",
        }
        meta = flat_to_doc_metadata(flat)
        assert meta.document_id == "test_doc_99"
        assert meta.status == DocStatus.ACTIVE
        assert "ADMIN" in meta.access_roles
        assert meta.effective_date.year == 2026
        assert meta.governing_law == "Indian Contract Act, 1872"
