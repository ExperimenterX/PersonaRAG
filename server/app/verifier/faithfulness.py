# app/verifier/faithfulness.py
from __future__ import annotations

from typing import List, Dict, Any
import re


class FaithfulnessVerifier:
    """
    Simple lexical faithfulness checker.

    For each sentence in the answer, we check whether a reasonable
    proportion of its words appear in the concatenated contexts.

    This is not as strong as an LLM verifier, but:
      - it's cheap,
      - deterministic,
      - and gives non-trivial support rates (not always 1.0).
    """

    def __init__(self, min_sentence_len: int = 6, overlap_threshold: float = 0.4):
        """
        :param min_sentence_len: minimum number of tokens to consider a sentence.
        :param overlap_threshold: fraction of sentence tokens that must appear in
                                  the context to count as "supported".
        """
        self.min_sentence_len = min_sentence_len
        self.overlap_threshold = overlap_threshold

    def _split_sentences(self, text: str) -> List[str]:
        # Super simple sentence splitter on '.', '?', '!'
        parts = re.split(r"[\.!\?]+", text)
        return [p.strip() for p in parts if p.strip()]

    def _tokenize(self, text: str) -> List[str]:
        # Lowercase, remove punctuation, split on whitespace
        text = text.lower()
        text = re.sub(r"[^a-z0-9]+", " ", text)
        return [t for t in text.split() if t]

    def verify(self, answer: str, contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Concatenate all context texts
        ctx_text = " ".join(
            c.get("content", "") for c in contexts if isinstance(c.get("content", ""), str)
        )
        ctx_tokens = set(self._tokenize(ctx_text))

        sentences = self._split_sentences(answer)
        if not sentences:
            # No content to check; treat as trivially faithful
            return {"support_rate": 1.0, "total_sentences": 0, "supported_sentences": 0}

        total = 0
        supported = 0

        for sent in sentences:
            tokens = self._tokenize(sent)
            if len(tokens) < self.min_sentence_len:
                # Too short / generic to evaluate robustly; skip
                continue

            total += 1
            if not ctx_tokens:
                continue

            overlap = sum(1 for t in tokens if t in ctx_tokens)
            frac = overlap / len(tokens)

            if frac >= self.overlap_threshold:
                supported += 1

        if total == 0:
            # All sentences were too short; be neutral but not perfect
            return {"support_rate": 0.5, "total_sentences": 0, "supported_sentences": 0}

        support_rate = supported / total
        return {
            "support_rate": support_rate,
            "total_sentences": total,
            "supported_sentences": supported,
        }
