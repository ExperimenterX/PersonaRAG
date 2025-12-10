from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

EMBED_MODEL = "intfloat/e5-base-v2"   # dense retriever
EMBED_DIM = 768

# chunking
CHUNK_SIZE = 600
CHUNK_OVERLAP = 120

# retrieval
K_DENSE = 50
K_BM25 = 50           # used if you enable BM25 (optional)
K_RERANK = 8          # final passages to send to generator

# fusion weight (dense vs bm25). If no BM25, this is ignored.
ALPHA = 0.65          # 0..1 -> higher favors dense similarity

# files
FAISS_PATH = ARTIFACTS_DIR / "faiss.index"
DOCSTORE_PATH = ARTIFACTS_DIR / "docstore.jsonl"   # simple dump of chunks for lookup
