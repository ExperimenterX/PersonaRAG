# app/retrieval/hybrid.py
from __future__ import annotations

from typing import List, Dict, Any
from collections import defaultdict

from app.retrieval.dense import DenseRetriever
from app.retrieval.bm25 import BM25Retriever
from app.core.config import ALPHA, K_DENSE, K_BM25, DOCSTORE_PATH


class HybridRetriever:
    """
    Hybrid = Dense (FAISS + E5) + BM25 (rank_bm25 over docstore.jsonl).
    Fuses scores via weighted sum after normalization.
    """

    def __init__(self):
        self.dense = DenseRetriever()
        self.bm25 = BM25Retriever(DOCSTORE_PATH)

    @staticmethod
    def _key_of(doc: Dict[str, Any]) -> str:
        """
        Create a stable key per document.
        Prefer chunk_id if present; otherwise hash of content.
        """
        meta = doc.get("meta") or {}
        chunk_id = meta.get("chunk_id")
        if chunk_id is not None:
            return f"chunk:{chunk_id}"
        return f"hash:{hash(doc['content'])}"

    @staticmethod
    def _normalize_scores(scores: Dict[str, float]) -> Dict[str, float]:
        if not scores:
            return {}
        vals = list(scores.values())
        lo, hi = min(vals), max(vals)
        if hi - lo < 1e-9:
            # all equal → treat as 1.0 so they still contribute
            return {k: 1.0 for k in scores}
        return {k: (v - lo) / (hi - lo) for k, v in scores.items()}

    def retrieve(
        self,
        query: str,
        k_dense: int = K_DENSE,
        k_bm25: int = K_BM25,
        alpha: float = ALPHA,
        top_cap: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Return a fused list of documents with:
        - content: str
        - meta: {..., dense_score?, bm25_score?, hybrid_score}
        """
        # 1) Dense retrieval using your existing DenseRetriever.topk
        dense_hits_raw = self.dense.topk(query, k=k_dense)
        dense_docs: List[Dict[str, Any]] = []
        for h in dense_hits_raw:
            meta = h.get("meta") or {}
            dense_docs.append(
                {
                    "content": h["content"],
                    "meta": {
                        **meta,
                        "dense_score": float(h.get("score", 0.0)),
                    },
                }
            )

        # 2) BM25 retrieval over docstore.jsonl
        bm25_docs = self.bm25.retrieve(query, top_k=k_bm25)

        # 3) Build combined dictionaries keyed by doc key
        all_docs: Dict[str, Dict[str, Any]] = {}
        dense_scores: Dict[str, float] = {}
        bm25_scores: Dict[str, float] = {}

        for d in dense_docs:
            k = self._key_of(d)
            all_docs[k] = d
            ds = d["meta"].get("dense_score")
            if ds is not None:
                dense_scores[k] = float(ds)

        for d in bm25_docs:
            k = self._key_of(d)
            if k not in all_docs:
                all_docs[k] = d
            bs = d["meta"].get("bm25_score")
            if bs is not None:
                bm25_scores[k] = float(bs)

        # 4) Normalize and fuse
        dense_norm = self._normalize_scores(dense_scores)
        bm25_norm = self._normalize_scores(bm25_scores)

        fused_scores = defaultdict(float)
        for k in all_docs.keys():
            d = dense_norm.get(k, 0.0)
            b = bm25_norm.get(k, 0.0)
            fused_scores[k] = alpha * d + (1.0 - alpha) * b

        # 5) Sort by fused score and attach hybrid_score
        ranked_keys = sorted(
            fused_scores.keys(),
            key=lambda kk: fused_scores[kk],
            reverse=True,
        )[:top_cap]

        results: List[Dict[str, Any]] = []
        for k in ranked_keys:
            doc = all_docs[k]
            meta = doc.get("meta") or {}
            meta["hybrid_score"] = float(fused_scores[k])
            results.append(
                {
                    "content": doc["content"],
                    "meta": meta,
                }
            )

        return results
