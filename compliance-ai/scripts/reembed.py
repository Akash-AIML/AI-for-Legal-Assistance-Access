"""Re-embed every chunk already stored in Chroma using the configured embedding model.

The old collection was created with 64-dim offline embeddings and is
dimension-locked, so we delete and recreate it at the correct dimension. All
text + metadata (including admin-uploaded docs like TCS/LangChain) is preserved;
only vector embeddings are recomputed.

Run from repo root:  .venv/bin/python scripts/reembed.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "src"))

import chromadb  # noqa: E402
from config import get_settings  # noqa: E402
from ingestion import store  # noqa: E402
from llm import embed_texts  # noqa: E402

s = get_settings()
client = chromadb.PersistentClient(path=s.chroma_dir)
name = s.collection_name

old = client.get_or_create_collection(name)
data = old.get(include=["documents", "metadatas"])
ids = data.get("ids", []) or []
texts = data.get("documents", []) or []
metas = data.get("metadatas", []) or []
print(f"read {len(ids)} chunks from existing collection")

client.delete_collection(name)
print("deleted old collection")

col = client.get_or_create_collection(name, metadata={"hnsw:space": "cosine"})

BATCH = 32
total = 0
for i in range(0, len(ids), BATCH):
    b_ids = ids[i : i + BATCH]
    b_texts = texts[i : i + BATCH]
    b_metas = metas[i : i + BATCH]
    embs = embed_texts(b_texts)
    col.upsert(ids=b_ids, embeddings=embs, documents=b_texts, metadatas=b_metas)
    total += len(b_ids)
    print(f"  upserted {total}/{len(ids)} (dim={len(embs[0])})")

store.rebuild_index()
print("done. re-embedded", total, "chunks at dim", len(embs[0]))