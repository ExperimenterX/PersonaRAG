from __future__ import annotations

import argparse
import csv
import json
import string
import time
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from app.core.config import DOCSTORE_PATH, K_BM25, K_DENSE, K_RERANK
from app.generation.generator import generate_answer
from app.rerank.bge_reranker import CrossEncoderReranker
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.dense import DenseRetriever
from app.retrieval.hybrid import HybridRetriever
from app.verifier.faithfulness import FaithfulnessVerifier


AVAILABLE_MODES = ["dense_only", "bm25_only", "hybrid", "hybrid_rerank"]
AVAILABLE_BENCHMARKS = ["hotpotqa", "nq", "triviaqa", "multireqa", "custom"]


@dataclass
class QAExample:
    qid: str
    question: str
    answers: List[str]


def normalize_text(text: str) -> str:
    text = (text or "").lower().strip()
    text = "".join(ch for ch in text if ch not in string.punctuation)
    return " ".join(text.split())


def exact_match(prediction: str, gold_answers: List[str]) -> float:
    pred = normalize_text(prediction)
    if not gold_answers:
        return 0.0
    return 1.0 if any(pred == normalize_text(g) for g in gold_answers if g) else 0.0


def token_f1(prediction: str, gold_answers: List[str]) -> float:
    pred_tokens = normalize_text(prediction).split()
    if not pred_tokens or not gold_answers:
        return 0.0

    best = 0.0
    pred_counts: Dict[str, int] = {}
    for token in pred_tokens:
        pred_counts[token] = pred_counts.get(token, 0) + 1

    for gold in gold_answers:
        gold_tokens = normalize_text(gold).split()
        if not gold_tokens:
            continue

        gold_counts: Dict[str, int] = {}
        for token in gold_tokens:
            gold_counts[token] = gold_counts.get(token, 0) + 1

        common = 0
        for token, count in pred_counts.items():
            common += min(count, gold_counts.get(token, 0))

        if common == 0:
            continue

        precision = common / len(pred_tokens)
        recall = common / len(gold_tokens)
        f1 = (2 * precision * recall) / (precision + recall)
        best = max(best, f1)

    return best


def answer_present_in_contexts(answers: List[str], contexts: List[Dict[str, Any]]) -> float:
    if not answers or not contexts:
        return 0.0

    joined = "\n".join(c.get("content", "") for c in contexts).lower()
    valid_answers = [a.strip().lower() for a in answers if a and a.strip()]
    if not valid_answers:
        return 0.0
    return 1.0 if any(ans in joined for ans in valid_answers) else 0.0


def _coerce_answers(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: List[str] = []
        for item in value:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                if "text" in item and isinstance(item["text"], str):
                    out.append(item["text"])
        return out
    if isinstance(value, dict):
        out: List[str] = []
        for key in ("text", "aliases", "normalized_aliases", "value"):
            if key not in value:
                continue
            v = value[key]
            if isinstance(v, str):
                out.append(v)
            elif isinstance(v, list):
                out.extend(x for x in v if isinstance(x, str))
        return out
    return []


def _extract_first(record: Dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in record and record[key] is not None:
            return record[key]
    return None


def load_custom_json(path: Path, limit: int) -> List[QAExample]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if not isinstance(payload, list):
        raise ValueError("Custom file must contain a list of examples.")

    items = payload[:limit] if limit > 0 else payload
    examples: List[QAExample] = []
    for i, row in enumerate(items):
        if not isinstance(row, dict):
            continue
        q = _extract_first(row, ["question", "query", "q"])
        if not isinstance(q, str) or not q.strip():
            continue
        ans = _coerce_answers(_extract_first(row, ["answers", "answer", "gold_answers"]))
        qid = str(_extract_first(row, ["id", "qid", "uid"]) or f"custom_{i+1}")
        examples.append(QAExample(qid=qid, question=q, answers=ans))
    return examples


def load_hf_examples(
    benchmark: str,
    split: str,
    limit: int,
    dataset_name: Optional[str],
    dataset_config: Optional[str],
) -> List[QAExample]:
    try:
        from datasets import load_dataset  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "The 'datasets' package is required for benchmark evaluation. "
            "Install it with: pip install datasets"
        ) from exc

    default_source: Dict[str, Tuple[str, Optional[str]]] = {
        "hotpotqa": ("hotpot_qa", "distractor"),
        "nq": ("nq_open", None),
        "triviaqa": ("trivia_qa", "rc.nocontext"),
        "multireqa": ("multi_reqa", None),
    }

    ds_name, ds_cfg = default_source.get(benchmark, (benchmark, None))
    if dataset_name:
        ds_name = dataset_name
    if dataset_config is not None:
        ds_cfg = dataset_config

    if ds_cfg:
        ds = load_dataset(ds_name, ds_cfg, split=split)
    else:
        ds = load_dataset(ds_name, split=split)

    if limit > 0:
        ds = ds.select(range(min(limit, len(ds))))

    examples: List[QAExample] = []
    for idx, row in enumerate(ds):
        if not isinstance(row, dict):
            continue

        question = _extract_first(row, ["question", "query", "input"])
        if not isinstance(question, str) or not question.strip():
            continue

        answer_candidates: List[str] = []
        for key in [
            "answer",
            "answers",
            "target",
            "gold",
            "labels",
            "output",
            "expected_answer",
        ]:
            answer_candidates.extend(_coerce_answers(row.get(key)))

        # TriviaQA usually stores aliases inside nested answer object.
        if "answer" in row and isinstance(row["answer"], dict):
            answer_candidates.extend(_coerce_answers(row["answer"]))

        # Hotpot can include answer directly in "answer".
        # NQ open can include list in "answer".

        deduped = []
        seen = set()
        for item in answer_candidates:
            n = normalize_text(item)
            if not n or n in seen:
                continue
            seen.add(n)
            deduped.append(item)

        qid = str(_extract_first(row, ["id", "qid", "example_id"]) or f"{benchmark}_{idx+1}")
        examples.append(QAExample(qid=qid, question=question, answers=deduped))

    return examples


def load_benchmark_examples(args: argparse.Namespace) -> List[QAExample]:
    if args.benchmark == "custom":
        if not args.input_file:
            raise ValueError("--input-file is required when --benchmark custom")
        return load_custom_json(Path(args.input_file), args.limit)

    return load_hf_examples(
        benchmark=args.benchmark,
        split=args.split,
        limit=args.limit,
        dataset_name=args.dataset_name,
        dataset_config=args.dataset_config,
    )


def build_pipeline(mode: str):
    dense = bm25 = hybrid = reranker = None

    if mode == "dense_only":
        dense = DenseRetriever()
    elif mode == "bm25_only":
        bm25 = BM25Retriever(DOCSTORE_PATH)
    elif mode in ("hybrid", "hybrid_rerank"):
        hybrid = HybridRetriever()
        if mode == "hybrid_rerank":
            reranker = CrossEncoderReranker(enabled=True)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    return dense, bm25, hybrid, reranker


def retrieve_topk(
    mode: str,
    query: str,
    dense: Optional[DenseRetriever],
    bm25: Optional[BM25Retriever],
    hybrid: Optional[HybridRetriever],
    reranker: Optional[CrossEncoderReranker],
) -> List[Dict[str, Any]]:
    if mode == "dense_only":
        assert dense is not None
        pool_raw = dense.topk(query, k=K_DENSE)
    elif mode == "bm25_only":
        assert bm25 is not None
        pool_raw = bm25.retrieve(query, top_k=K_BM25)
    else:
        assert hybrid is not None
        pool_raw = hybrid.retrieve(query, top_cap=100)

    if mode == "hybrid_rerank" and reranker is not None:
        return reranker.rerank(query, pool_raw, k=K_RERANK)
    return pool_raw[:K_RERANK]


def _safe_name(text: str) -> str:
    out = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in text.strip())
    return out.strip("_") or "run"


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_summary_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "benchmark",
        "split",
        "mode",
        "limit",
        "examples_evaluated",
        "exact_match",
        "token_f1",
        "support_rate",
        "context_answer_recall_at_k",
        "latency_seconds",
        "timestamp_utc",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k) for k in fieldnames})


def evaluate_mode(
    mode: str,
    examples: List[QAExample],
    print_examples: int = 3,
) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
    print(f"\n=== Benchmark evaluation mode: {mode} ===")

    dense, bm25, hybrid, reranker = build_pipeline(mode)
    verifier = FaithfulnessVerifier()

    em_scores: List[float] = []
    f1_scores: List[float] = []
    support_rates: List[float] = []
    context_answer_recall: List[float] = []
    latencies: List[float] = []
    rows: List[Dict[str, Any]] = []

    total = len(examples)
    for idx, ex in enumerate(examples, start=1):
        t0 = time.perf_counter()
        topk = retrieve_topk(mode, ex.question, dense, bm25, hybrid, reranker)

        out = generate_answer(ex.question, topk)
        answer = out.get("answer", "")

        contexts = [
            {"i": i + 1, "content": c.get("content", ""), "meta": c.get("meta", {})}
            for i, c in enumerate(topk)
        ]

        ver = verifier.verify(answer, contexts)
        t1 = time.perf_counter()

        em = exact_match(answer, ex.answers)
        f1 = token_f1(answer, ex.answers)
        carr = answer_present_in_contexts(ex.answers, contexts)

        em_scores.append(em)
        f1_scores.append(f1)
        support_rates.append(ver.get("support_rate", 0.0))
        context_answer_recall.append(carr)
        latencies.append(t1 - t0)

        rows.append(
            {
                "id": ex.qid,
                "question": ex.question,
                "gold_answers": ex.answers,
                "prediction": answer,
                "exact_match": em,
                "token_f1": f1,
                "support_rate": ver.get("support_rate", 0.0),
                "context_answer_recall_at_k": carr,
                "latency_seconds": t1 - t0,
                "topk_contexts": contexts,
            }
        )

        if idx <= print_examples:
            print(f"\n[{mode}] Example {idx}/{total} | id={ex.qid}")
            print("Q:", ex.question)
            print("Gold answers:", ex.answers[:5])
            print("Pred:", answer)
            print("EM:", round(em, 3), "F1:", round(f1, 3), "Support:", round(ver.get("support_rate", 0.0), 3))

    def _avg(values: List[float]) -> float:
        return (sum(values) / len(values)) if values else 0.0

    metrics = {
        "exact_match": _avg(em_scores),
        "token_f1": _avg(f1_scores),
        "support_rate": _avg(support_rates),
        "context_answer_recall_at_k": _avg(context_answer_recall),
        "latency_seconds": _avg(latencies),
    }

    print("\n=== Aggregate Benchmark Metrics ===")
    print(f"Mode:                                 {mode}")
    print(f"Exact Match (EM):                     {metrics['exact_match']:.3f}")
    print(f"Token F1:                             {metrics['token_f1']:.3f}")
    print(f"Average Support Rate (verifier):      {metrics['support_rate']:.3f}")
    print(f"Context Answer Recall@K (proxy):      {metrics['context_answer_recall_at_k']:.3f}")
    print(f"Average End-to-End Latency (seconds): {metrics['latency_seconds']:.3f}")

    return metrics, rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate PersonaRAG on external QA benchmarks (HotpotQA, NQ, TriviaQA, MultiReQA) "
            "using existing retrieval/generation/verifier pipeline."
        )
    )
    parser.add_argument(
        "--benchmark",
        type=str,
        default="hotpotqa",
        choices=AVAILABLE_BENCHMARKS,
        help="Which benchmark loader to use.",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="hybrid_rerank",
        choices=AVAILABLE_MODES + ["all"],
        help="Retrieval mode to evaluate.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum number of examples to evaluate (<=0 means all).",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="validation",
        help="Dataset split name for Hugging Face datasets.",
    )
    parser.add_argument(
        "--dataset-name",
        type=str,
        default=None,
        help="Optional override for HF dataset name (useful for MultiReQA variants).",
    )
    parser.add_argument(
        "--dataset-config",
        type=str,
        default=None,
        help="Optional override for HF dataset config.",
    )
    parser.add_argument(
        "--input-file",
        type=str,
        default=None,
        help="Path to custom JSON file when --benchmark custom.",
    )
    parser.add_argument(
        "--print-examples",
        type=int,
        default=3,
        help="Number of examples to print with predictions.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Directory where benchmark result artifacts (json/csv/jsonl) are written.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    examples = load_benchmark_examples(args)

    if not examples:
        raise RuntimeError("No benchmark examples were loaded. Check benchmark/split/limit arguments.")

    print("=" * 80)
    print("PersonaRAG Benchmark Evaluation")
    print("=" * 80)
    print(f"Benchmark:        {args.benchmark}")
    print(f"Split:            {args.split}")
    print(f"Examples loaded:  {len(examples)}")
    print(f"Mode:             {args.mode}")
    print(f"Limit:            {args.limit}")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    run_key = f"{_safe_name(args.benchmark)}_{_safe_name(args.split)}_{_safe_name(args.mode)}_{timestamp}"

    summary_rows: List[Dict[str, Any]] = []

    if args.mode == "all":
        summary: Dict[str, Dict[str, float]] = {}
        for mode in AVAILABLE_MODES:
            metric, detail_rows = evaluate_mode(mode, examples, print_examples=args.print_examples)
            summary[mode] = metric

            detail_path = output_dir / f"{run_key}_{mode}_details.jsonl"
            _write_jsonl(detail_path, detail_rows)

            summary_rows.append(
                {
                    "benchmark": args.benchmark,
                    "split": args.split,
                    "mode": mode,
                    "limit": args.limit,
                    "examples_evaluated": len(examples),
                    "exact_match": round(metric["exact_match"], 6),
                    "token_f1": round(metric["token_f1"], 6),
                    "support_rate": round(metric["support_rate"], 6),
                    "context_answer_recall_at_k": round(metric["context_answer_recall_at_k"], 6),
                    "latency_seconds": round(metric["latency_seconds"], 6),
                    "timestamp_utc": timestamp,
                }
            )

        print("\n" + "=" * 80)
        print("Summary Across Modes")
        print("=" * 80)
        for mode in AVAILABLE_MODES:
            metric = summary[mode]
            print(
                f"{mode:14s} | EM={metric['exact_match']:.3f} | F1={metric['token_f1']:.3f} | "
                f"Support={metric['support_rate']:.3f} | ContextRecall={metric['context_answer_recall_at_k']:.3f} | "
                f"Latency={metric['latency_seconds']:.3f}s"
            )

        summary_json = output_dir / f"{run_key}_summary.json"
        summary_csv = output_dir / f"{run_key}_summary.csv"
        _write_json(summary_json, {"run_key": run_key, "rows": summary_rows})
        _write_summary_csv(summary_csv, summary_rows)
        print(f"\nSaved summary JSON: {summary_json}")
        print(f"Saved summary CSV:  {summary_csv}")
    else:
        metric, detail_rows = evaluate_mode(args.mode, examples, print_examples=args.print_examples)

        summary_rows.append(
            {
                "benchmark": args.benchmark,
                "split": args.split,
                "mode": args.mode,
                "limit": args.limit,
                "examples_evaluated": len(examples),
                "exact_match": round(metric["exact_match"], 6),
                "token_f1": round(metric["token_f1"], 6),
                "support_rate": round(metric["support_rate"], 6),
                "context_answer_recall_at_k": round(metric["context_answer_recall_at_k"], 6),
                "latency_seconds": round(metric["latency_seconds"], 6),
                "timestamp_utc": timestamp,
            }
        )

        detail_path = output_dir / f"{run_key}_{args.mode}_details.jsonl"
        summary_json = output_dir / f"{run_key}_summary.json"
        summary_csv = output_dir / f"{run_key}_summary.csv"

        _write_jsonl(detail_path, detail_rows)
        _write_json(summary_json, {"run_key": run_key, "rows": summary_rows})
        _write_summary_csv(summary_csv, summary_rows)

        print(f"\nSaved details JSONL: {detail_path}")
        print(f"Saved summary JSON:  {summary_json}")
        print(f"Saved summary CSV:   {summary_csv}")


if __name__ == "__main__":
    main()
