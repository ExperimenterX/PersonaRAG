from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any

from docx import Document as DocxDocument
from pypdf import PdfReader

from app.indexing.loader import flatten_resume_pack


def extract_pdf(path: Path) -> str:
    try:
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages.append(text)
        return "\n".join(pages)
    except Exception as e:
        print(f"[WARN] Failed to read PDF {path}: {e}")
        return ""


def extract_docx(path: Path) -> str:
    try:
        doc = DocxDocument(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        print(f"[WARN] Failed to read DOCX {path}: {e}")
        return ""


def extract_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"[WARN] Failed to read text file {path}: {e}")
        return ""


def load_all_sources(data_dir: Path) -> List[Dict[str, Any]]:
    """
    Load:
      - resume_pack.json (structured)
      - everything under data/docs/ (pdf, docx, txt, md)
    Returns list of blocks: {section, text, source}
    """
    blocks: List[Dict[str, Any]] = []

    # 1) Structured resume JSON
    resume_file = data_dir / "resume.json"
    if resume_file.exists():
        for b in flatten_resume_pack(resume_file):
            blocks.append({
                "section": f"resume::{b['section']}",
                "text": b["text"],
                "source": "resume.json",
            })

    # 2) Generic docs under data/docs (recursive)
    docs_root = data_dir / "docs"
    if docs_root.exists():
        for path in docs_root.rglob("*"):
            if path.is_dir():
                continue

            suffix = path.suffix.lower()
            text = ""

            if suffix in {".txt", ".md"}:
                text = extract_text_file(path)
            elif suffix == ".pdf":
                text = extract_pdf(path)
            elif suffix == ".docx":
                text = extract_docx(path)
            else:
                # skip .doc, images, etc. for now
                print(f"[INFO] Skipping unsupported file type: {path}")
                continue

            if not text or not text.strip():
                print(f"[INFO] Empty or unreadable file skipped: {path}")
                continue

            blocks.append({
                "section": f"file::{path.stem}",
                "text": text,
                "source": str(path.relative_to(data_dir)),
            })

    print(f"[INFO] Loaded {len(blocks)} logical blocks from JSON + docs/")
    return blocks
