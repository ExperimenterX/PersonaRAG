# app/retrieval/bm25.py
from __future__ import annotations
from app.core.utils import expand_query
from typing import List, Dict, Any
from pathlib import Path
import json

from rank_bm25 import BM25Okapi


class BM25Retriever:
    """
    Lightweight BM25 over your docstore.jsonl.
    Uses 'content' as document text, keeps meta for provenance.
    """

    def __init__(self, docstore_path: Path):
        self.docstore_path = docstore_path
        self.docs: List[Dict[str, Any]] = []
        self.tokenized_corpus: List[List[str]] = []
        self.bm25: BM25Okapi | None = None

        self._load()

    def _load(self):
        assert self.docstore_path.exists(), f"Docstore not found: {self.docstore_path}"

        self.docs = []
        with self.docstore_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                # expected keys: chunk_id, section, source, content
                self.docs.append(
                    {
                        "content": obj["content"],
                        "meta": {
                            "section": obj.get("section"),
                            "source": obj.get("source"),
                            "chunk_id": obj.get("chunk_id"),
                        },
                    }
                )

        def tokenize(text: str) -> List[str]:
            # very simple tokenization; you can improve later
            return text.lower().split()

        self.tokenized_corpus = [tokenize(d["content"]) for d in self.docs]
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        print(f"[BM25] Loaded {len(self.docs)} docs from {self.docstore_path}")

    def retrieve(self, query: str, top_k: int = 50) -> List[Dict[str, Any]]:
        if not self.docs or self.bm25 is None:
            return []

        expanded_query = expand_query(query)
        tokens = expanded_query.lower().split()
        scores = self.bm25.get_scores(tokens)

        # sort docs by score desc, keep top_k
        ranked_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:top_k]

        results = []
        for i in ranked_indices:
            d = self.docs[i]
            results.append(
                {
                    "content": d["content"],
                    "meta": {**d["meta"], "bm25_score": float(scores[i])},
                }
            )
        return results
