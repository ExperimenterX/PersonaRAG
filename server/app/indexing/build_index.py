from typing import List
from pathlib import Path

from haystack.document_stores import FAISSDocumentStore
from haystack.nodes import EmbeddingRetriever
from haystack import Document

from app.core.config import (
    DATA_DIR,
    FAISS_PATH,
    DOCSTORE_PATH,
    EMBED_DIM,
    EMBED_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)
from app.indexing.chunker import chunk_text
from app.indexing.multi_loader import load_all_sources
from app.core.utils import save_jsonl


def _reset_faiss_state():
    # Remove old FAISS index + JSONL dump
    for p in [FAISS_PATH, DOCSTORE_PATH]:
        if p.exists():
            print(f"[INFO] Removing existing file: {p}")
            p.unlink()

    # Remove any Haystack SQL/config leftovers
    for p in Path(".").glob("faiss_document_store*"):
        print(f"[INFO] Removing existing Haystack file: {p}")
        p.unlink()


def build():
    assert DATA_DIR.exists(), f"DATA_DIR does not exist: {DATA_DIR}"

    _reset_faiss_state()

    # 1) Load normalized content (JSON + docs/)
    raw_blocks = load_all_sources(DATA_DIR)

    # 2) Fresh FAISS store with *default* on-disk SQL DB
    store = FAISSDocumentStore(
        embedding_dim=EMBED_DIM,
        faiss_index_factory_str="HNSW32",  # or "Flat"
    )

    retriever = EmbeddingRetriever(
        document_store=store,
        embedding_model=EMBED_MODEL,
        model_format="sentence_transformers",
    )

    docs: List[Document] = []
    dump_rows = []
    idx = 0

    for b in raw_blocks:
        text = b["text"]
        section = b["section"]
        source = b["source"]

        for chunk in chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP):
            meta = {
                "section": section,
                "chunk_id": idx,
                "source": source,
            }
            docs.append(Document(content=chunk, meta=meta))
            dump_rows.append(
                {
                    "chunk_id": idx,
                    "section": section,
                    "source": source,
                    "content": chunk,
                }
            )
            idx += 1

    print(f"[INFO] Writing {len(docs)} chunks into FAISS store...")
    store.write_documents(docs)

    print("[INFO] Computing embeddings and updating FAISS index...")
    store.update_embeddings(retriever)

    print(f"[INFO] Saving FAISS index to {FAISS_PATH}")
    store.save(FAISS_PATH)

    print(f"[INFO] Dumping docstore JSONL to {DOCSTORE_PATH}")
    save_jsonl(DOCSTORE_PATH, dump_rows)

    print(f"✅ Indexed {len(docs)} chunks → {FAISS_PATH} and {DOCSTORE_PATH}")


if __name__ == "__main__":
    build()
