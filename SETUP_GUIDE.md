# PersonaRAG Setup & Development Guide

This guide provides detailed instructions for setting up, developing, and deploying PersonaRAG.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Setup](#quick-setup)
- [Manual Setup](#manual-setup)
- [Development Workflow](#development-workflow)
- [Adding Your Own Data](#adding-your-own-data)
- [Troubleshooting](#troubleshooting)
- [Deployment](#deployment)

---

## Prerequisites

### Required Software

1. **Python 3.11**
   - Windows: Download from [python.org](https://www.python.org/downloads/)
   - Linux: `sudo apt install python3.11 python3.11-venv`
   - Mac: `brew install python@3.11`

2. **Node.js 16+**
   - Download from [nodejs.org](https://nodejs.org/)
   - Or use nvm: `nvm install 16`

3. **Git**
   - Windows: Download from [git-scm.com](https://git-scm.com/)
   - Linux: `sudo apt install git`
   - Mac: `brew install git`

### Optional

- **OpenAI API Key** (for LLM generation)
- **Docker** (for containerized deployment)

---

## Quick Setup

### Windows (PowerShell)

```powershell
# Clone repository
git clone https://github.com/ExperimenterX/PersonaRAG.git
cd PersonaRAG

# Run automated setup
.\setup.ps1

# Start application
.\start.ps1
```

### Linux/Mac (Bash)

```bash
# Clone repository
git clone https://github.com/ExperimenterX/PersonaRAG.git
cd PersonaRAG

# Make scripts executable
chmod +x setup.sh start.sh

# Run automated setup
./setup.sh

# Start application
./start.sh
```

The application will be available at: **http://localhost:8000**

---

## Manual Setup

If you prefer manual setup or the automated scripts don't work:

### Step 1: Backend Setup

```bash
# Navigate to project root
cd PersonaRAG

# Create Python 3.11 virtual environment
py -3.11 -m venv server/venv311          # Windows
python3.11 -m venv server/venv311        # Linux/Mac

# Activate virtual environment
.\server\venv311\Scripts\activate        # Windows PowerShell
server\venv311\Scripts\activate.bat      # Windows CMD
source server/venv311/bin/activate       # Linux/Mac

# Upgrade pip
python -m pip install --upgrade pip

# Install Python dependencies
pip install -r server/requirements.txt
```

### Step 2: Frontend Setup

```bash
# Navigate to client directory
cd client

# Install Node.js dependencies
npm install

# Build production bundle
npm run build

# Return to root
cd ..
```

### Step 3: Build FAISS Index

```bash
# Navigate to server directory
cd server

# Build index (first time or after data changes)
python -m app.indexing.build_index
```

This will:
- Load `data/resume.json`
- Process files in `data/docs/`
- Create FAISS index in `artifacts/faiss.index`
- Save document store to `artifacts/docstore.jsonl`

### Step 4: Start Server

```bash
# Make sure you're in server directory
cd server

# Start FastAPI server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server endpoints:
- Frontend: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

---

## Development Workflow

### Frontend Development

For hot-reload during frontend development:

```bash
cd client

# Start Vite dev server (hot reload)
npm run dev
```

This starts the dev server on http://localhost:5173

Update `ChatWidget.vue` to point to backend:
```javascript
const API_BASE_URL = 'http://127.0.0.1:8000'
```

### Backend Development

The `--reload` flag in uvicorn automatically reloads on code changes:

```bash
cd server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing Changes

1. **API Testing**: Use http://localhost:8000/docs (Swagger UI)
2. **Frontend Testing**: Open http://localhost:8000 or http://localhost:5173
3. **Run Evaluation**: `python -m app.eval.run_eval`

### Code Structure

```
server/app/
├── main.py              # FastAPI app & routes
├── core/
│   ├── config.py        # Configuration & constants
│   └── utils.py         # Helper functions
├── indexing/
│   ├── build_index.py   # Index building
│   ├── loader.py        # JSON loading
│   ├── chunker.py       # Text chunking
│   └── multi_loader.py  # Multi-format loading
├── retrieval/
│   ├── dense.py         # FAISS retrieval
│   ├── hybrid.py        # Hybrid retrieval
│   └── sparse.py        # BM25 retrieval
├── rerank/
│   └── bge_reranker.py  # Cross-encoder reranking
└── generation/
    └── generator.py     # LLM generation & verification
```

---

## Adding Your Own Data

### Structured Resume Data

Edit `server/data/resume.json`:

```json
{
  "name": "Your Name",
  "email": "your@email.com",
  "experience": [...],
  "projects": [...],
  "skills": {...},
  "certifications": [...],
  ...
}
```

### Document Files

Add files to `server/data/docs/`:

- **Supported formats**: PDF, DOCX, MD, TXT
- **Naming**: Use descriptive filenames (e.g., `resume-2024.pdf`)
- **Organization**: Can use subdirectories

Example:
```
server/data/docs/
├── resume-2024.pdf
├── cover-letter.docx
├── project-reports/
│   ├── project1.md
│   └── project2.pdf
└── certifications/
    ├── aws-cert.pdf
    └── azure-cert.pdf
```

### Rebuild Index

After adding/modifying data:

```bash
cd server
python -m app.indexing.build_index
```

This will:
1. Remove old index files
2. Load all data sources
3. Chunk documents (800 tokens, 100 overlap)
4. Generate embeddings (E5-base-v2)
5. Build FAISS index (HNSW32)
6. Save to `artifacts/`

---

## Configuration

### Environment Variables

Create `server/.env`:

```bash
# OpenAI API Key (required for LLM generation)
OPENAI_API_KEY=sk-...

# Embedding Model (default: intfloat/e5-base-v2)
EMBED_MODEL=intfloat/e5-base-v2

# Chunking Parameters
CHUNK_SIZE=800
CHUNK_OVERLAP=100

# Retrieval Parameters
K_DENSE=50
K_SPARSE=50
K_RERANK=8

# Generation Model
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.1
```

### Config File

Alternatively, edit `server/app/core/config.py`:

```python
# Data paths
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

# Embedding settings
EMBED_MODEL = "intfloat/e5-base-v2"
EMBED_DIM = 768

# Chunking settings
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

# Retrieval settings
K_RERANK = 8
```

---

## Troubleshooting

### Common Issues

#### 1. Python Version Error

**Error**: `TypeError: ForwardRef._evaluate() missing required argument 'recursive_guard'`

**Solution**: Ensure Python 3.11 (not 3.12+)
```bash
python --version  # Should show 3.11.x
```

#### 2. Port Already in Use

**Error**: `Address already in use: 0.0.0.0:8000`

**Solution**: Kill existing process
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

#### 3. Module Not Found

**Error**: `ModuleNotFoundError: No module named 'app'`

**Solution**: Run from `server/` directory
```bash
cd server
python -m app.indexing.build_index
```

#### 4. CORS Error

**Error**: `Access-Control-Allow-Origin header missing`

**Solution**: Already configured in `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 5. Frontend Not Loading

**Solution**: Rebuild frontend
```bash
cd client
npm run build
cd ..
# Restart server
```

#### 6. FAISS Index Error

**Error**: `FileNotFoundError: faiss.index not found`

**Solution**: Build index first
```bash
cd server
python -m app.indexing.build_index
```

---

## Deployment

### Local Production

```bash
# Build frontend
cd client
npm run build

# Start server with gunicorn (Linux/Mac)
cd ../server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or with uvicorn (Windows)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY server/ ./server/
COPY client/dist/ ./client/dist/

# Build index
WORKDIR /app/server
RUN python -m app.indexing.build_index

# Expose port
EXPOSE 8000

# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t personarag .
docker run -p 8000:8000 personarag
```

### Cloud Deployment (AWS/Azure/GCP)

1. Set up VM with Python 3.11 and Node.js
2. Clone repository
3. Run setup script
4. Configure reverse proxy (nginx/Apache)
5. Set up systemd service (Linux)
6. Configure firewall for port 8000

---

## Performance Optimization

### Backend

1. **Use GPU for embeddings** (if available):
   ```python
   device = "cuda" if torch.cuda.is_available() else "cpu"
   ```

2. **Increase workers**:
   ```bash
   uvicorn app.main:app --workers 4
   ```

3. **Cache embeddings**: Store precomputed embeddings

### Frontend

1. **Enable compression** in nginx:
   ```nginx
   gzip on;
   gzip_types application/javascript text/css;
   ```

2. **CDN for static assets**

3. **Lazy loading** for images

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

---

## Support

- 📧 Email: shankar.bhavani.in@gmail.com
- 🐙 GitHub Issues: [PersonaRAG/issues](https://github.com/ExperimenterX/PersonaRAG/issues)
- 💼 LinkedIn: [shankar-bhavani](https://www.linkedin.com/in/shankar-bhavani/)

---

## License

MIT License - see [LICENSE](LICENSE) file.
