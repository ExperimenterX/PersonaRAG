from typing import List, Dict, Any

# Plug in a real cross-encoder later (BAAI/bge-reranker-base).
# For now, pass-through to keep things simple & fast.
class CrossEncoderReranker:
    def __init__(self, enabled: bool = False):
        self.enabled = enabled

    def rerank(self, query: str, candidates: List[Dict[str, Any]], k: int = 8) -> List[Dict[str, Any]]:
        if not self.enabled:
            return candidates[:k]
        # TODO: implement Transformer cross-encoder scoring
        return candidates[:k]
