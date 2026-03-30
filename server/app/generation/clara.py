from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

import requests


def _as_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def clara_enabled() -> bool:
    return _as_bool(os.getenv("CLARA_ENABLED"), default=False)


def clara_strict() -> bool:
    return _as_bool(os.getenv("CLARA_STRICT"), default=False)


def clara_endpoint() -> str:
    return os.getenv("CLARA_ENDPOINT", "").rstrip("/")


def clara_timeout_seconds() -> float:
    raw = os.getenv("CLARA_TIMEOUT_SECONDS", "30")
    try:
        return float(raw)
    except ValueError:
        return 30.0


def _doc_fingerprint(docs: List[Dict[str, Any]]) -> str:
    payload = [
        {
            "content": d.get("content", ""),
            "meta": d.get("meta", {}),
        }
        for d in docs
    ]
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


_COMPRESS_CACHE: Dict[str, Any] = {}


def clara_generate(question: str, docs: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Stage-1 + Stage-2 adapter for CLaRA served behind HTTP endpoints.

    Expected API contract:
      POST {CLARA_ENDPOINT}/compress
        body: {
          "documents": [str, ...],
          "metas": [dict, ...],
          "compression_rate": int(optional)
        }
        response: {
          "compressed": Any,
          "doc_ids": [optional]
        }

      POST {CLARA_ENDPOINT}/answer
        body: {
          "question": str,
          "compressed": Any,
          "doc_ids": [optional]
        }
        response: {
          "answer": str,
          "citations": [optional]
        }

    If CLARA is disabled or endpoint is not configured/reachable, returns None.
    """
    if not clara_enabled():
        return None

    base = clara_endpoint()
    if not base:
        print("[CLaRA] CLARA_ENABLED=true but CLARA_ENDPOINT is empty. Falling back.")
        if clara_strict():
            return {
                "answer": "CLaRA strict mode is enabled, but CLARA_ENDPOINT is empty.",
                "citations": [],
                "backend": "clara",
            }
        return None

    timeout = clara_timeout_seconds()
    compression_rate_raw = os.getenv("CLARA_COMPRESSION_RATE", "32")
    try:
        compression_rate = int(compression_rate_raw)
    except ValueError:
        compression_rate = 32

    documents = [d.get("content", "") for d in docs]
    metas = [d.get("meta", {}) for d in docs]

    try:
        # Stage-1 compression (cached by doc set fingerprint)
        fprint = _doc_fingerprint(docs)
        compressed = _COMPRESS_CACHE.get(fprint)

        if compressed is None:
            compress_resp = requests.post(
                f"{base}/compress",
                json={
                    "documents": documents,
                    "metas": metas,
                    "compression_rate": compression_rate,
                },
                timeout=timeout,
            )
            compress_resp.raise_for_status()
            compressed = compress_resp.json()
            _COMPRESS_CACHE[fprint] = compressed

        # Stage-2 QA on compressed docs
        answer_resp = requests.post(
            f"{base}/answer",
            json={
                "question": question,
                "compressed": compressed.get("compressed", compressed),
                "doc_ids": compressed.get("doc_ids", []),
            },
            timeout=timeout,
        )
        answer_resp.raise_for_status()
        result = answer_resp.json()

        answer = result.get("answer", "")
        bridge_error = result.get("error") or result.get("last_hf_error")
        if isinstance(bridge_error, str) and bridge_error.strip():
            print(f"[CLaRA] Bridge reported error: {bridge_error}")
        if not isinstance(answer, str) or not answer.strip():
            print("[CLaRA] Empty answer payload. Falling back.")
            return None

        citations = result.get("citations")
        if not isinstance(citations, list):
            citations = [
                {
                    "i": i + 1,
                    "section": m.get("section"),
                    "chunk_id": m.get("chunk_id"),
                }
                for i, m in enumerate(metas)
            ]

        return {
            "answer": answer.strip(),
            "citations": citations,
            "backend": "clara",
        }

    except requests.RequestException as exc:
        print(f"[CLaRA] Request error: {exc}. Falling back.")
        if clara_strict():
            return {
                "answer": "I don't know.",
                "citations": [],
                "backend": "clara",
            }
        return None
    except Exception as exc:
        print(f"[CLaRA] Unexpected error: {exc}. Falling back.")
        if clara_strict():
            return {
                "answer": "I don't know.",
                "citations": [],
                "backend": "clara",
            }
        return None
