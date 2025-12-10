from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from app.retrieval.hybrid import HybridRetriever
from app.rerank.bge_reranker import CrossEncoderReranker
from app.verifier.faithfulness import FaithfulnessVerifier
from app.generation.generator import generate_answer, build_context
from app.core.config import K_RERANK
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="PersonaRAG API", version="0.1.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR.parent / "client" / "dist"

# Lazy initialization - load models only when needed
retriever = None
reranker = None
verifier = None

def get_retriever():
    global retriever
    if retriever is None:
        print("Initializing HybridRetriever...")
        retriever = HybridRetriever()
        print("HybridRetriever initialized!")
    return retriever

def get_reranker():
    global reranker
    if reranker is None:
        print("Initializing CrossEncoderReranker...")
        reranker = CrossEncoderReranker(enabled=False)
        print("CrossEncoderReranker initialized!")
    return reranker

def get_verifier():
    global verifier
    if verifier is None:
        from app.verifier.faithfulness import FaithfulnessVerifier
        print("Initializing FaithfulnessVerifier...")
        verifier = FaithfulnessVerifier()
        print("FaithfulnessVerifier initialized!")
    return verifier

@app.get("/health")
def health():
    print("Health check OK")
    return {"status": "ok"}

@app.get("/search")
def search(q: str = Query(..., min_length=1), k: int = 10):
    ret = get_retriever()
    pool = ret.retrieve(q, top_cap=max(k, K_RERANK))
    return {"query": q, "results": pool[:k]}

@app.get("/qa")
def qa(q: str = Query(..., min_length=1)):
    ret = get_retriever()
    rer = get_reranker()
    ver = get_verifier()

    #retrieval
    pool = ret.retrieve(q, top_cap=100)

    #reranking
    topk = rer.rerank(q, pool, k=K_RERANK)

    #generation
    out = generate_answer(q, topk)
    answer = out["answer"]

    contexts = [
        {"i": i + 1, "content": c["content"], "meta": c["meta"]}
        for i, c in enumerate(topk)
    ]

    #verification
    ver_result = ver.verify(answer, contexts)

    return {
        "question": q,
        "answer": out["answer"],
        "citations": out["citations"],
        "contexts": contexts,
        "verification": ver_result,
    }

# Mount static files (must be after API routes)
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")
    print(f"[INFO] Mounted static assets from: {FRONTEND_DIST / 'assets'}")
else:
    print(f"[WARN] Frontend dist directory does not exist: {FRONTEND_DIST}")

# Serve frontend (catch-all route must be last)
@app.get("/{full_path:path}", include_in_schema=False)
async def serve_frontend(full_path: str):
    """Serve the Vue.js frontend for all non-API routes"""
    index_path = FRONTEND_DIST / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    else:
        return {"error": "Frontend not built. Run 'npm run build' in the client directory."}
