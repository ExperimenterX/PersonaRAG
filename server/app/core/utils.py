
from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any

def save_jsonl(path: Path, rows: List[Dict[str, Any]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows

def expand_query(q: str) -> str:
    """
    Very lightweight, domain-specific query expansion.

    - Adds synonyms for contact info, projects, skills, etc.
    - Keeps the original query words so we don't lose intent.
    """

    q_lower = q.lower()

    # Base tokens from original query
    base_tokens: List[str] = q_lower.split()

    # Domain-specific synonym buckets
    expansions: List[str] = []

    # Contact / identity
    if any(w in q_lower for w in ["mail", "email", "e-mail", "contact", "reach"]):
        expansions += [
            "email", "e-mail", "contact", "address",
            "linkedin", "github", "portfolio", "website"
        ]

    if "linkedin" in q_lower:
        expansions += ["linkedin", "profile", "linked in", "social"]

    if "github" in q_lower or "git hub" in q_lower:
        expansions += ["github", "git hub", "repos", "repository", "code"]

    if "portfolio" in q_lower or "website" in q_lower or "site" in q_lower:
        expansions += ["portfolio", "website", "personal site", "projects"]

    # Projects
    if "project" in q_lower or "projects" in q_lower:
        expansions += ["projects", "apps", "applications", "work"]

    # Skills / tech stack
    if "skills" in q_lower or "tech stack" in q_lower:
        expansions += ["skills", "technologies", "tools", "languages"]

    # Experience / work history
    if any(w in q_lower for w in ["experience", "worked", "job", "role", "position"]):
        expansions += ["experience", "work history", "professional", "employment"]

    # Education
    if any(w in q_lower for w in ["education", "degree", "university", "college"]):
        expansions += ["education", "degree", "university", "masters", "bachelor"]

    # Very small clean-up: remove obvious duplicates
    all_tokens = base_tokens + expansions
    deduped = []
    seen = set()
    for t in all_tokens:
        if t not in seen:
            seen.add(t)
            deduped.append(t)

    # Build expanded query string
    expanded_query = " ".join(deduped)
    # Optional: debug print
    # print(f"[expand_query] '{q}' -> '{expanded_query}'")
    return expanded_query
