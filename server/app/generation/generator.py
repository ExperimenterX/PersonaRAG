# app/generation/generator.py
from __future__ import annotations

import os
from typing import List, Dict, Any

from dotenv import load_dotenv
from openai import OpenAI

# Load .env (searches up the directory tree)
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is not set. Please define it in your environment or .env file."
    )

client = OpenAI(api_key=OPENAI_API_KEY)

def current_date() -> str:
    from datetime import datetime

    return datetime.now().strftime("%B %d, %Y")

def build_context(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize docs into a list of context blocks:
      [{ "i": int, "content": str, "meta": {...} }, ...]
    `docs` is what main.py passes in: a list of dicts with 'content' and 'meta'.
    """
    contexts: List[Dict[str, Any]] = []
    for i, d in enumerate(docs, start=1):
        contexts.append(
            {
                "i": i,
                "content": d.get("content", ""),
                "meta": d.get("meta", {}) or {},
            }
        )
    return contexts


def _build_rag_prompt(question: str, contexts: List[Dict[str, Any]]) -> str:
    """
    Build a RAG-style prompt from question + contexts.
    """
    blocks = []
    for c in contexts:
        i = c["i"]
        content = c["content"]
        src = c["meta"].get("source", "unknown")
        section = c["meta"].get("section", "")
        header = f"[{i}] source: {src}"
        if section:
            header += f" | section: {section}"
        blocks.append(f"{header}\n{content}")

    context_text = "\n\n".join(blocks)

    prompt = f"""You are a Personnel AI assistant for Bhavani Shankar that answers questions about Bhavani Shankar's background, work experience, projects, skills, and certifications.

Use ONLY the information in the CONTEXT below. If the context does not contain the answer, say you don't know.

QUESTION:
{question}

CONTEXT:
{context_text}

INSTRUCTIONS:
- Answer concisely in natural language.
- Combine information from multiple snippets if needed.
- Do NOT invent facts that are not supported by the context.
- If something is unclear or missing, say that it's not available.
- current date: {current_date()}
- use emojis to keep the tone friendly and engaging, don't give AI responses and respond like a human expert.
- if any context contains link references, write them as a link which can be clicked.
Now provide your answer.
"""
    return prompt


def generate_answer(question: str, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main entry point used by main.py:
      - docs: list of { "content": str, "meta": {...} } from reranker
      - returns: { "answer": str, "citations": [...] }
    """
    contexts = build_context(docs)
    prompt = _build_rag_prompt(question, contexts)

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise, grounded assistant. "
                    "Never hallucinate facts outside the provided context."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    answer = response.choices[0].message.content.strip()

    # Simple citation mapping: 1..N in the same order as contexts
    citations = [
        {
            "i": c["i"],
            "section": c["meta"].get("section"),
            "chunk_id": c["meta"].get("chunk_id"),
        }
        for c in contexts
    ]

    return {
        "answer": answer,
        "citations": citations,
    }
