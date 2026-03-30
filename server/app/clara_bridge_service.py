from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from huggingface_hub import InferenceClient


load_dotenv()


app = FastAPI(title="PersonaRAG CLaRA Bridge", version="0.1.0")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

CLARA_PROVIDER = os.getenv("CLARA_PROVIDER", "openai").strip().lower()
CLARA_HF_MODEL = os.getenv("CLARA_HF_MODEL", "apple/CLaRa-7B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN", "")
hf_client = InferenceClient(token=HF_TOKEN) if HF_TOKEN else InferenceClient()
LAST_HF_ERROR = ""


def _set_hf_error(message: str) -> None:
    global LAST_HF_ERROR
    LAST_HF_ERROR = message[:500]


def _clear_hf_error() -> None:
    global LAST_HF_ERROR
    LAST_HF_ERROR = ""


def _answer_with_hf(prompt: str) -> str:
    errors: List[str] = []

    def _err(exc: Exception) -> str:
        text = str(exc).strip()
        return text if text else repr(exc)

    try:
        out = hf_client.text_generation(
            prompt=prompt,
            model=CLARA_HF_MODEL,
            max_new_tokens=128,
            temperature=0.2,
            do_sample=False,
            return_full_text=False,
        )
        text = (out or "").strip()
        if text:
            _clear_hf_error()
            return text
        errors.append("text_generation returned empty output")
    except Exception as exc:
        errors.append(f"text_generation: {_err(exc)}")

    try:
        chat_api = getattr(hf_client, "chat", None)
        if chat_api is not None and hasattr(chat_api, "completions"):
            resp = chat_api.completions.create(
                model=CLARA_HF_MODEL,
                messages=[
                    {"role": "system", "content": "Answer only from context. If unknown, say I don't know."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=128,
            )
            text = (resp.choices[0].message.content or "").strip()
            if text:
                _clear_hf_error()
                return text
            errors.append("chat.completions returned empty output")
        else:
            errors.append("chat.completions API unavailable in installed huggingface_hub")
    except Exception as exc:
        errors.append(f"chat.completions: {_err(exc)}")

    if not HF_TOKEN:
        errors.append("HF_TOKEN is not set")

    msg = " | ".join(errors)
    _set_hf_error(msg)
    return "I don't know."


class CompressRequest(BaseModel):
    documents: List[str]
    metas: Optional[List[Dict[str, Any]]] = None
    compression_rate: Optional[int] = 32


class AnswerRequest(BaseModel):
    question: str
    compressed: Any
    doc_ids: Optional[List[str]] = None


def _compress_text(text: str, compression_rate: int) -> str:
    if not text:
        return ""
    words = text.split()
    if compression_rate <= 1:
        keep = len(words)
    else:
        keep = max(24, len(words) // compression_rate)
    return " ".join(words[:keep])


@app.get("/health")
def health() -> Dict[str, Any]:
    if CLARA_PROVIDER == "huggingface":
        backend = f"huggingface:{CLARA_HF_MODEL}"
    elif CLARA_PROVIDER == "openai":
        backend = "openai" if client else "none"
    else:
        backend = "none"

    return {
        "status": "ok",
        "service": "clara-bridge",
        "model_backend": backend,
        "model": CLARA_HF_MODEL if CLARA_PROVIDER == "huggingface" else OPENAI_MODEL,
        "hf_token_configured": bool(HF_TOKEN),
        "last_hf_error": LAST_HF_ERROR,
    }


@app.post("/compress")
def compress(req: CompressRequest) -> Dict[str, Any]:
    rate = req.compression_rate or 32
    compressed_docs = [_compress_text(d, rate) for d in req.documents]
    doc_ids = [str(i) for i in range(len(compressed_docs))]
    return {
        "compressed": compressed_docs,
        "doc_ids": doc_ids,
    }


@app.post("/answer")
def answer(req: AnswerRequest) -> Dict[str, Any]:
    compressed = req.compressed
    if isinstance(compressed, dict) and "compressed" in compressed:
        compressed = compressed["compressed"]

    if isinstance(compressed, list):
        context_text = "\n\n".join(
            f"[{i+1}] {str(chunk)}" for i, chunk in enumerate(compressed)
        )
    else:
        context_text = str(compressed)

    prompt = (
        "You are CLaRA-style QA over compressed documents. "
        "Answer only using provided context. If unknown, say 'I don't know.'\n\n"
        f"Question:\n{req.question}\n\n"
        f"Compressed Context:\n{context_text}\n\n"
        "Answer:"
    )

    if CLARA_PROVIDER == "huggingface":
        text = _answer_with_hf(prompt)
    elif CLARA_PROVIDER == "openai":
        if client is None:
            text = "I don't know."
        else:
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Be concise and factual."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            text = (resp.choices[0].message.content or "").strip()
    else:
        text = "I don't know."
    citations = []
    if isinstance(req.doc_ids, list):
        citations = [{"doc_id": d} for d in req.doc_ids]

    return {
        "answer": text,
        "citations": citations,
        "error": LAST_HF_ERROR if CLARA_PROVIDER == "huggingface" else "",
    }
