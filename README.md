# 🧠 PersonaRAG
> LLM-augmented Information Retrieval (IR) & Question Answering over a personal knowledge corpus (resume, projects, docs).

![Licensed Under](./LICENSE)

PersonaRAG retrieves evidence from a curated personal corpus and generates grounded answers with inline citations. The system uses **hybrid retrieval (Dense + BM25)**, **cross-encoder reranking**, a **grounded LLM generator**, and a **Verifier** that filters unsupported sentences.

---

## ✨ Features
- **Hybrid Retrieval**: Dense embeddings (E5) + BM25 fusion for high recall
- **Cross-Encoder Reranking**: `BAAI/bge-reranker-base` for precise ordering
- **Grounded Generation**: LLM answers strictly from retrieved context
- **Verifier**: Sentence-level support check with visual indicators (green/yellow/red dots)
- **FastAPI Backend**: `/health`, `/search`, `/qa` endpoints with CORS support
- **Vue.js Frontend**: Interactive chat interface with typing animations and clickable links
- **Support Rate Visualization**: Real-time confidence indicators for answers
- **Comprehensive Indexing**: Processes JSON, PDF, DOCX, Markdown, and text files

---

## 🧩 Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11), Pydantic v1
- **Dense Retrieval**: Sentence-Transformers (`intfloat/e5-base-v2`) + FAISS (HNSW32)
- **Sparse Retrieval**: BM25 via Rank-BM25
- **Reranker**: `BAAI/bge-reranker-base` (cross-encoder)
- **Generation**: OpenAI GPT-4 (configurable)
- **Verifier**: Embedding similarity for sentence-level support
- **Document Processing**: PyPDF, python-docx, JSON

### Frontend
- **Framework**: Vue 3 + Vite
- **Features**: Real-time chat, markdown link parsing, typing animations
- **Styling**: Custom CSS with gradient backgrounds and hover effects

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.11** (required for Pydantic v1 compatibility)
- **Node.js 16+** (for frontend build)
- **Git**

### Setup (Windows)

```powershell
# 1. Clone the repository
git clone https://github.com/ExperimenterX/PersonaRAG.git
cd PersonaRAG

# 2. Run setup script
.\setup.ps1

# 3. Start the application
.\start.ps1

# 4. Open browser
# Navigate to http://localhost:8000
```

### Setup (Linux/Mac)

```bash
# 1. Clone the repository
git clone https://github.com/ExperimenterX/PersonaRAG.git
cd PersonaRAG

# 2. Make scripts executable
chmod +x setup.sh start.sh

# 3. Run setup script
./setup.sh

# 4. Start the application
./start.sh

# 5. Open browser
# Navigate to http://localhost:8000
```

---

## 📁 Project Structure

```
PersonaRAG/
├── client/                  # Vue.js frontend
│   ├── src/
│   │   ├── App.vue         # Main app component
│   │   ├── components/
│   │   │   └── ChatWidget.vue  # Chat interface
│   │   └── main.js
│   ├── package.json
│   └── vite.config.js
│
├── server/                  # FastAPI backend
│   ├── app/
│   │   ├── main.py         # API endpoints
│   │   ├── core/           # Configuration
│   │   ├── indexing/       # Document processing
│   │   ├── retrieval/      # Hybrid retrieval
│   │   ├── rerank/         # Cross-encoder reranking
│   │   └── generation/     # LLM generation
│   ├── data/
│   │   ├── resume.json     # Structured resume data
│   │   ├── docs/           # PDF, DOCX, MD files
│   │   └── eval_set.json   # Evaluation questions
│   ├── artifacts/          # Generated indices
│   │   ├── faiss.index
│   │   └── docstore.jsonl
│   ├── requirements.txt
│   └── venv311/            # Python virtual environment
│
├── setup.ps1               # Windows setup script
├── setup.sh                # Linux/Mac setup script
├── start.ps1               # Windows start script
├── start.sh                # Linux/Mac start script
├── eval.ps1                # Windows evaluation script
├── eval.sh                 # Linux/Mac evaluation script
└── README.md
```

---

## 🔧 Manual Setup (Alternative)

### Backend Setup

```powershell
# Create Python 3.11 virtual environment
py -3.11 -m venv server\venv311

# Activate virtual environment
.\server\venv311\Scripts\activate  # Windows
source server/venv311/bin/activate  # Linux/Mac

# Install dependencies
pip install -r server\requirements.txt

# Build FAISS index
cd server
python -m app.indexing.build_index
```

### Frontend Setup

```bash
# Install dependencies
cd client
npm install

# Build for production
npm run build

# Or run development server
npm run dev
```

### Start Server

```bash
cd server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🎯 Usage

### Chat Interface

1. Open http://localhost:8000 in your browser
2. Click the chat icon (💬) in the bottom-right corner
3. Ask questions like:
   - "What programming languages does Bhavani know?"
   - "Tell me about his experience at Bosch"
   - "What certifications does he have?"
   - "Show me his GitHub profile"

### Support Rate Indicators

Each AI response shows a colored dot indicating confidence:
- 🟢 **Green (≥60%)**: High confidence - answer strongly supported
- 🟡 **Yellow (30-60%)**: Medium confidence - partial support
- 🔴 **Red (<30%)**: Low confidence - limited support
- ⚪ **Gray**: No verification data

Click the ⓘ icon in the chat header to learn more about PersonaRAG.

### API Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Search
```bash
curl "http://localhost:8000/search?q=machine%20learning&k=5"
```

#### Question Answering
```bash
curl "http://localhost:8000/qa?q=What%20are%20Bhavani's%20skills"
```

Response format:
```json
{
  "question": "What are Bhavani's skills?",
  "answer": "Bhavani has expertise in...",
  "citations": [...],
  "contexts": [...],
  "verification": {
    "support_rate": 0.85,
    "total_sentences": 2,
    "supported_sentences": 2
  }
}
```

---

## 📊 Evaluation

Evaluate the system performance using the automated evaluation suite with 35 test questions.

### Quick Evaluation

**Windows:**
```powershell
# Run with default mode (hybrid_rerank - full pipeline)
.\eval.ps1

# Test specific retrieval mode
.\eval.ps1 dense_only
.\eval.ps1 bm25_only
.\eval.ps1 hybrid
.\eval.ps1 hybrid_rerank

# Run all modes for comprehensive comparison
.\eval.ps1 all
```

**Linux/Mac:**
```bash
# Run with default mode (hybrid_rerank - full pipeline)
./eval.sh

# Test specific retrieval mode
./eval.sh dense_only
./eval.sh bm25_only
./eval.sh hybrid
./eval.sh hybrid_rerank

# Run all modes for comprehensive comparison
./eval.sh all
```

### Evaluation Modes

1. **`dense_only`** - Dense retrieval using FAISS embeddings only
2. **`bm25_only`** - Sparse retrieval using BM25 only
3. **`hybrid`** - Combines dense + BM25 (no reranking)
4. **`hybrid_rerank`** - Full pipeline with cross-encoder reranking ⭐ (recommended)
5. **`all`** - Runs all 4 modes sequentially for comparison

### Evaluation Metrics

Each evaluation provides:
- **Retrieval Recall@10**: Section-level recall (0-1)
- **Average Support Rate**: Answer faithfulness (0-1)
- **Average Keyword Hit Rate**: QA quality proxy (0-1)
- **Average Latency**: End-to-end response time (seconds)

### Manual Evaluation

```bash
cd server

# Run with default mode
python -m app.eval.run_eval

# Run specific mode
python -m app.eval.run_eval --mode dense_only
python -m app.eval.run_eval --mode bm25_only
python -m app.eval.run_eval --mode hybrid
python -m app.eval.run_eval --mode hybrid_rerank

# Run all modes
python -m app.eval.run_eval --mode all

# Get help
python -m app.eval.run_eval --help
```

### Sample Output

```
=== Evaluating mode: hybrid_rerank ===

=== Example q1 ===
Q: What programming languages does Bhavani know?
Relevant sections (gold): ['skills']
Top-10 sections: ['resume::skills', ...]
Answer: Bhavani knows 6 programming languages: Python, Golang, JavaScript...
Support rate: 0.85
Keyword hit rate: 1.0
Latency (s): 2.34

...

=== Aggregate Metrics ===
Mode:                                     hybrid_rerank
Retrieval Recall@10 (section-level):      0.943
Average Support Rate (verifier):          0.812
Average Keyword Hit Rate (QA proxy):      0.867
Average End-to-End Latency (seconds):     2.156
```

---
python -m app.eval.run_eval
```

This tests:
- Retrieval accuracy
- Answer quality
- Citation correctness
- Keyword presence
- Support rate verification

---

## 🛠️ Configuration

### Environment Variables

Create `.env` file in `server/` directory:

```bash
OPENAI_API_KEY=your-api-key-here
EMBED_MODEL=intfloat/e5-base-v2
```

### Adding Your Own Data

1. **Structured data**: Edit `server/data/resume.json`
2. **Documents**: Add PDF, DOCX, MD, or TXT files to `server/data/docs/`
3. **Rebuild index**: Run `python -m app.indexing.build_index`

---

## 🐛 Troubleshooting

### Port 8000 already in use
```bash
# Find and kill the process
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Linux/Mac
```

### Python version issues
- Ensure Python 3.11 is installed (Pydantic v1 requires <3.12)
- Use `py -3.11` on Windows or `python3.11` on Linux/Mac

### CORS errors
- Backend includes CORS middleware for `localhost:5173` and `*`
- Check browser console for specific errors

### Frontend not loading
- Rebuild: `cd client && npm run build`
- Check `client/dist/` folder exists
- Restart server to serve new build

---

## 📝 License

License - see [LICENSE](LICENSE) file for details

---

## 👤 Author

**Bhavani Shankar**
- 📧 Email: shankar.bhavani.in@gmail.com
- 💼 LinkedIn: [linkedin.com/in/shankar-bhavani](https://www.linkedin.com/in/shankar-bhavani/)
- 🐙 GitHub: [github.com/ExperimenterX](https://github.com/ExperimenterX)
- 🌐 Portfolio: [shankarbhavani-fs.github.io](https://shankarbhavani-fs.github.io/)

---

## 🙏 Acknowledgments

- Sentence Transformers by Hugging Face
- FAISS by Meta AI
- FastAPI by Sebastián Ramírez
- Vue.js by Evan You
- BGE models by BAAI

---

## 📚 References

- [Retrieval-Augmented Generation (RAG)](https://arxiv.org/abs/2005.11401)
- [Dense Passage Retrieval](https://arxiv.org/abs/2004.04906)
- [BGE: Better Text Embeddings](https://arxiv.org/abs/2309.07597)
- [FAISS: Billion-scale similarity search](https://arxiv.org/abs/1702.08734)

