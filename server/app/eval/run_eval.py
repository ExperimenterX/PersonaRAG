# app/eval/run_eval.py
from __future__ import annotations

from typing import List, Dict, Any
from pathlib import Path
import json
import time
import argparse

from app.retrieval.hybrid import HybridRetriever
from app.retrieval.dense import DenseRetriever
from app.retrieval.bm25 import BM25Retriever
from app.rerank.bge_reranker import CrossEncoderReranker
from app.generation.generator import generate_answer
from app.verifier.faithfulness import FaithfulnessVerifier
from app.core.config import K_RERANK, DATA_DIR, DOCSTORE_PATH, K_DENSE, K_BM25

# Available evaluation modes
AVAILABLE_MODES = ["dense_only", "bm25_only", "hybrid", "hybrid_rerank"]


def load_eval_set(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_section(sec: str | None) -> str | None:
    """
    Strip prefixes like 'resume::' or 'docs::' so labels like 'projects[0]'
    match both 'projects[0]' and 'resume::projects[0]'.
    """
    if sec is None:
        return None
    for prefix in ("resume::", "docs::"):
        if sec.startswith(prefix):
            return sec[len(prefix):]
    return sec


def section_is_relevant(section: str | None, relevant_sections: List[str]) -> bool:
    """
    Consider a section hit if:
      - exact match after normalization, or
      - the gold label is a prefix of the normalized section, e.g.
        'experience' matches 'experience[0]' and 'experience[1]'.
    """
    if not section:
        return False
    s_norm = normalize_section(section)
    if not s_norm:
        return False

    for rel in relevant_sections:
        rel_norm = normalize_section(rel)
        if not rel_norm:
            continue
        if s_norm == rel_norm:
            return True
        # Coarse label like "experience" should match "experience[0]" etc.
        if s_norm.startswith(rel_norm + "["):
            return True
    return False


def keyword_hit_rate(answer: str, keywords: List[str]) -> float:
    """
    Simple QA utility metric:
    fraction of gold keywords that appear in the answer (case-insensitive).
    """
    if not keywords:
        return 0.0
    ans_l = answer.lower()
    hits = sum(1 for kw in keywords if kw.lower() in ans_l)
    return hits / len(keywords)


def evaluate(eval_mode: str):
    eval_path = DATA_DIR / "eval_set.json"
    assert eval_path.exists(), f"Eval set not found: {eval_path}"

    examples = load_eval_set(eval_path)

    print(f"=== Evaluating mode: {eval_mode} ===")

    # Instantiate the components we need ONCE
    dense = bm25 = hybrid = reranker = None

    if eval_mode == "dense_only":
        dense = DenseRetriever()
    elif eval_mode == "bm25_only":
        bm25 = BM25Retriever(DOCSTORE_PATH)
    elif eval_mode in ("hybrid", "hybrid_rerank"):
        hybrid = HybridRetriever()
        if eval_mode == "hybrid_rerank":
            reranker = CrossEncoderReranker(enabled=True)
    else:
        raise ValueError(f"Unknown eval_mode: {eval_mode}")

    verifier = FaithfulnessVerifier()

    total = len(examples)
    hit_at_10 = 0
    support_rates: List[float] = []
    keyword_scores: List[float] = []
    latencies: List[float] = []

    for ex in examples:
        q = ex["question"]
        relevant_sections = ex.get("relevant_sections", [])
        gold_keywords = ex.get("keywords", [])

        print(f"\n=== Example {ex['id']} ===")
        print("Q:", q)
        print("Relevant sections (gold):", relevant_sections)

        t0 = time.perf_counter()

        # 1) retrieval (depends on mode)
        if eval_mode == "dense_only":
            pool_raw = dense.topk(q, k=K_DENSE)
        elif eval_mode == "bm25_only":
            pool_raw = bm25.retrieve(q, top_k=K_BM25)
        else:  # hybrid or hybrid_rerank
            pool_raw = hybrid.retrieve(q, top_cap=100)

        # 2) reranking (if enabled)
        if eval_mode == "hybrid_rerank" and reranker is not None:
            topk = reranker.rerank(q, pool_raw, k=K_RERANK)
        else:
            topk = pool_raw[:K_RERANK]

        # --- Retrieval metric: Recall@10 (section-level) ---
        top10 = topk[:10]
        sections_top10 = [c["meta"].get("section") for c in top10]
        print("Top-10 sections:", sections_top10)

        hit = any(section_is_relevant(s, relevant_sections) for s in sections_top10)
        if hit:
            hit_at_10 += 1

        # 3) generation
        out = generate_answer(q, topk)
        answer = out["answer"]
        contexts = [
            {"i": i + 1, "content": c["content"], "meta": c["meta"]}
            for i, c in enumerate(topk)
        ]

        # 4) verification (faithfulness)
        ver_result = verifier.verify(answer, contexts)
        support_rates.append(ver_result["support_rate"])

        # 5) keyword-based QA metric
        kw_score = keyword_hit_rate(answer, gold_keywords)
        keyword_scores.append(kw_score)

        t1 = time.perf_counter()
        latencies.append(t1 - t0)

        print("Answer:", answer)
        print("Support rate:", ver_result["support_rate"])
        print("Keyword hit rate:", kw_score)
        print("Latency (s):", t1 - t0)

    retrieval_recall_at_10 = hit_at_10 / total if total else 0.0
    avg_support_rate = sum(support_rates) / len(support_rates) if support_rates else 0.0
    avg_keyword_hit_rate = sum(keyword_scores) / len(keyword_scores) if keyword_scores else 0.0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    print("\n=== Aggregate Metrics ===")
    print(f"Mode:                                     {eval_mode}")
    print(f"Retrieval Recall@10 (section-level):      {retrieval_recall_at_10:.3f}")
    print(f"Average Support Rate (verifier):          {avg_support_rate:.3f}")
    print(f"Average Keyword Hit Rate (QA proxy):      {avg_keyword_hit_rate:.3f}")
    print(f"Average End-to-End Latency (seconds):     {avg_latency:.3f}")


def main():
    parser = argparse.ArgumentParser(
        description="PersonaRAG Evaluation Script - Compare different retrieval modes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default mode (hybrid_rerank)
  python -m app.eval.run_eval

  # Test dense retrieval only
  python -m app.eval.run_eval --mode dense_only

  # Test BM25 retrieval only
  python -m app.eval.run_eval --mode bm25_only

  # Test hybrid (no reranking)
  python -m app.eval.run_eval --mode hybrid

  # Test full pipeline with reranking
  python -m app.eval.run_eval --mode hybrid_rerank

  # Run all modes for comparison
  python -m app.eval.run_eval --mode all
        """
    )
    
    parser.add_argument(
        "--mode", "-m",
        type=str,
        default="hybrid_rerank",
        choices=AVAILABLE_MODES + ["all"],
        help="Evaluation mode to run. Options: %(choices)s. Use 'all' to run all modes sequentially."
    )
    
    args = parser.parse_args()
    
    if args.mode == "all":
        print("=" * 80)
        print("Running evaluation on ALL modes")
        print("=" * 80)
        
        results = {}
        for mode in AVAILABLE_MODES:
            print(f"\n{'=' * 80}")
            print(f"Starting evaluation for mode: {mode}")
            print(f"{'=' * 80}\n")
            
            evaluate(mode)
            
            print(f"\n{'=' * 80}")
            print(f"Completed evaluation for mode: {mode}")
            print(f"{'=' * 80}\n")
        
        print("\n" + "=" * 80)
        print("ALL EVALUATIONS COMPLETED")
        print("=" * 80)
        print("\nYou can now compare the aggregate metrics from each mode above.")
    else:
        evaluate(args.mode)


if __name__ == "__main__":
    main()
