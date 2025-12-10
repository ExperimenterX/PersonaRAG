from haystack.document_stores import FAISSDocumentStore
from haystack.nodes import EmbeddingRetriever
from typing import List, Dict, Any
from app.core.config import FAISS_PATH, EMBED_MODEL, K_DENSE

class DenseRetriever:
    def __init__(self):
        self.store = FAISSDocumentStore.load(FAISS_PATH)
        self.retriever = EmbeddingRetriever(
            document_store=self.store,
            embedding_model=EMBED_MODEL,
            model_format="sentence_transformers"
        )
        print(f"[DenseRetriever] Loaded FAISS index from {FAISS_PATH}")

    def topk(self, query: str, k: int = K_DENSE) -> List[Dict[str, Any]]:
        docs = self.retriever.retrieve(query=query, top_k=k)
        out = []
        for d in docs:
            out.append({
                "content": d.content,
                "score": float(d.score or 0.0),
                "meta": dict(d.meta)
            })
        return out
