# Rag Builder

Build a complete RAG (Retrieval Augmented Generation) system from your SQL dump, JSON, or Excel files. Creates a searchable vector database with Qdrant and a FastAPI endpoint for querying.

## Features

- **Multiple data formats**: SQL dumps, JSON, Excel, CSV
- **Auto GPU/CPU detection**: Uses BGE-M3 on GPU, multilingual-e5-small on CPU
- **Auto vector dimensions**: Detects correct embedding dimensions based on model
- **Flexible metadata**: Preserves all fields from your data
- **Docker or local**: Run everything in Docker or locally with uv
- **Qdrant vector DB**: Fast semantic search with cosine similarity

## Quick Start

```bash
# 1. Clone or copy this repo
git clone https://github.com/nakul-nsksystem/rag-builder.git
cd rag-builder

# 2. Edit .env with your settings
cp .env.example .env
# Edit .env - set your LLM URL, data file, etc.

# 3. Start Docker services
docker compose up -d

# 4. Install Python deps and ingest data
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
uv run python -m src.ingest

# 5. Start API
uv run uvicorn src.main:app --host 0.0.0.0 --port 8769
```

API available at: http://localhost:8769/docs

---

## Installation for AI Coding Tools

This skill can be used with AI coding assistants like **opencode** and **Claude Code**.

### opencode

Copy the `rag-builder` folder to your opencode skills directory:

```bash
cp -r rag-builder ~/.config/opencode/skills/rag-builder
```

Then restart opencode. The skill will be automatically loaded when you ask about building RAG systems.

**File structure for opencode:**
```
~/.config/opencode/skills/rag-builder/
├── SKILL.md          # Skill instructions (required)
├── src/              # Source code
├── scripts/          # Helper scripts
├── data/             # Data folder
├── requirements.txt  # Python dependencies
├── docker-compose.yml # Docker setup
├── Dockerfile        # Docker image
├── .env.example      # Configuration template
└── README.md        # This file
```

### Claude Code

Copy the `rag-builder` folder to your Claude skills directory:

```bash
cp -r rag-builder ~/.claude/skills/rag-builder
```

Or for project-specific skills:

```bash
cp -r rag-builder /path/to/your/project/.claude/skills/rag-builder
```

**File structure for Claude Code:**
```
~/.claude/skills/rag-builder/
├── SKILL.md          # Skill instructions (required)
├── src/              # Source code
├── scripts/          # Helper scripts
├── data/             # Data folder
├── requirements.txt  # Python dependencies
├── docker-compose.yml # Docker setup
├── Dockerfile        # Docker image
├── .env.example      # Configuration template
└── README.md        # This file
```

---

## Configuration

Edit `.env` file:

```bash
# LLM Configuration
LLM_BASE_URL=http://host.docker.internal:1234/v1
LLM_MODEL=llama-3
LLM_TEMPERATURE=0.2

# Embeddings - auto-detects GPU vs CPU and vector dimensions
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=cuda
CPU_EMBEDDING_MODEL=intfloat/multilingual-e5-small
VECTOR_SIZE=0  # Auto-detect (set manually if using custom model)

# Chunking
CHUNK_SIZE=600
CHUNK_OVERLAP=100

# Vector Database
QDRANT_URL=http://qdrant:6333
COLLECTION_NAME=rag_collection

# Data - put your file in data/ folder
DATA_PATH=./data/exported_data.json

# API Server
API_HOST=0.0.0.0
API_PORT=8769
```

### Embedding Models

| Model | Dimensions | Best For |
|-------|------------|----------|
| BAAI/bge-m3 | 1024 | Multilingual (Japanese, Chinese, 100+ languages) |
| intfloat/multilingual-e5-small | 384 | Fast CPU inference |
| sentence-transformers/all-MiniLM-L6-v2 | 384 | English only, fastest |

### Vector Dimensions

Vector dimensions are auto-detected based on the model. Known models:

| Model | Dimensions |
|-------|------------|
| BAAI/bge-m3 | 1024 |
| BAAI/bge-large-zh-v1.5 | 1024 |
| BAAI/bge-base-zh-v1.5 | 768 |
| intfloat/multilingual-e5-small | 384 |
| intfloat/multilingual-e5-base | 768 |
| sentence-transformers/all-MiniLM-L6-v2 | 384 |
| sentence-transformers/all-mpnet-base-v2 | 768 |

---

## Data Formats

### RAG Format (Recommended)

```json
[
  {
    "text": "Searchable text content here",
    "metadata": {
      "id": "record-123",
      "category": "support",
      "any_other_field": "value"
    }
  }
]
```

### Raw Text Array (Auto-converted)

```json
["Text entry 1", "Text entry 2", "Text entry 3"]
```

### Raw Object Array (Auto-converted)

```json
[
  {"question": "How do I...", "answer": "You can..."},
  {"question": "Why does...", "answer": "Because..."}
]
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/rag/query` | POST | Query with LLM synthesis |
| `/rag/search` | POST | Pure vector search (no LLM) |
| `/rag/ingest` | POST | Re-ingest data |
| `/health` | GET | Health check |
| `/` | GET | API info |

### Example Query

```bash
curl -X POST http://localhost:8769/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Your question here", "top_k": 5}'
```

---

## Docker Commands

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Rebuild (after code changes)
docker compose up -d --build

# Run ingestion manually
docker compose exec rag-api uv run python -m src.ingest
```

---

## Local Development

```bash
# Create venv
uv venv && source .venv/bin/activate

# Install deps
uv pip install -r requirements.txt

# Run ingestion
uv run python -m src.ingest

# Run API
uv run uvicorn src.main:app --reload

# Run tests (if any)
uv run pytest
```

---

## Project Structure

```
rag-builder/
├── src/
│   ├── __init__.py
│   ├── config.py       # Settings with auto GPU/CPU detection
│   ├── ingest.py       # Data ingestion pipeline
│   ├── rag.py          # RAG query system
│   └── main.py         # FastAPI server
├── scripts/
│   └── convert_data.py # Data format conversion
├── data/               # Put your data files here
├── vectors/            # Qdrant storage (created automatically)
├── docker-compose.yml  # Docker services
├── Dockerfile          # Docker image
├── requirements.txt    # Python dependencies
├── .env.example        # Configuration template
├── SKILL.md            # AI assistant skill instructions
└── README.md           # This file
```

---

## Troubleshooting

### "Module not found"
```bash
uv pip install -r requirements.txt
```

### "Data file not found"
Check `DATA_PATH` in `.env` matches your file location.

### "Embedding dimension mismatch"
Make sure `VECTOR_SIZE` in `.env` matches your model's dimensions, or set to `0` for auto-detection.

### "Cannot connect to Qdrant"
```bash
curl http://localhost:6533/health
```
If using Docker, make sure containers are running: `docker ps`

### "Cannot connect to LLM"
- Make sure LM Studio is running with "Start Server" clicked
- Check `LLM_BASE_URL` in `.env` is correct

---

## License

MIT - Do whatever you want.
