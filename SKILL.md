---
name: rag-builder
description: Build a RAG system from SQL, JSON, or Excel data with Qdrant vector database and FastAPI. Creates searchable vector DB with embeddings.
---

# SQL RAG Builder

Build a complete RAG (Retrieval Augmented Generation) system from your SQL dump or extracted data files.

## IMPORTANT RULES

**NEVER run these commands yourself - they take too long and will timeout:**
- `docker compose up -d --build`
- `docker compose up -d`
- `uv run python -m src.ingest`
- `uv run python -m src.main`
- Any build, ingestion, or long-running commands

**INSTEAD:**
1. Give the user the **EXACT command** to run
2. Print it clearly so they can copy-paste
3. Wait for them to confirm it's done
4. Then verify the result

Example:
```
"Please run these commands in your terminal:

# 1. Start Docker services
docker compose up -d

# 2. Ingest data (this takes a while)
source .venv/bin/activate && uv run python -m src.ingest

Once each command finishes, let me know and I'll verify it's working."
```

**Always use `uv run python` for running Python scripts (not just `python`).**
"Please run this command in your terminal:
docker compose up -d --build or docker-compose up -d

Once it's done, let me know and I'll verify it's working."
```

---

## Recommended: Docker Setup (All-in-One)

**This is the recommended approach** - everything runs in Docker containers:
- Qdrant vector database
- RAG API server  
- Python virtual environment (created automatically inside container)
- All Python dependencies

### Quick Start with Docker

```bash
# 1. Copy the skill files to your project
# 2. Prepare your data (see Step 3 below) and save to data/your_file.json
# 3. Set DATA_FILE=your_file.json in .env

# Give user these commands:
# 1. Start Docker services
docker compose up -d

# 2. Install Python dependencies
uv venv && source .venv/bin/activate && uv pip install -r requirements.txt

# 3. Ingest data (takes a while depending on size)
source .venv/bin/activate && uv run python -m src.ingest

# 4. Start API
source .venv/bin/activate && uv run uvicorn src.main:app --host 0.0.0.0 --port 8769
```

**API is now running at http://localhost:8769**

### Port & Project Configuration

**IMPORTANT: Before starting Docker, ask the user:**
- "Do you have anything running on port 6533 (Qdrant) or 8769 (API)? If yes, what ports should I use?"
- "What should I name this project?" (used for container names to avoid conflicts)

Set these in `.env`:
```bash
PROJECT_NAME=myproject       # Prefix for container names (unique per project)
QDRANT_PORT=6533             # External port for Qdrant
API_PORT=8769                # External port for API
DATA_FILE=my_data.json       # Your data filename in data/ folder
```

**Running multiple projects:**
Each project should have a unique `PROJECT_NAME` to avoid container name conflicts:
```bash
# Project 1
PROJECT_NAME=support docker compose up -d

# Project 2
PROJECT_NAME=products docker compose up -d
```

Containers will be named `{PROJECT_NAME}-qdrant` and `{PROJECT_NAME}-api`.

### For Data Ingestion

**IMPORTANT: Do NOT run this yourself. Give user the command:**

```bash
# Give user this command to run:
docker exec -it rag-api python -m src.ingest

# This command takes a long time (depends on data size)
# Wait for user to confirm it's done
# Then verify with: docker exec qdrant-rag curl http://localhost:6333/collections
```

---

## Alternative: Local Setup with uv (No Docker)

If you prefer running without Docker, use `uv` for fast dependency management:

### Prerequisites

- Python 3.10+ (uv handles this)
- LM Studio running at `http://192.168.0.194:1234` (or your configured IP)
- `uv` installed: `pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Quick Setup with uv

```bash
# 1. Create virtual environment
uv venv && source .venv/bin/activate  # Linux/macOS
# uv venv && .\.venv\Scripts\Activate  # Windows

# 2. Install dependencies
uv pip install -r requirements.txt

# 3. Copy and edit env file
cp .env.example .env
# Edit .env with your settings

# 4. Start Qdrant (required)
docker compose up -d qdrant

# 5. Ingest data
uv run python -m src.ingest

# 6. Start API
uv run uvicorn src.main:app --host 0.0.0.0 --port 8769
```

**API runs at http://localhost:8769**

## Supported Input Formats

1. **SQL dump files** (`.sql`) - Parse and extract specific tables
2. **JSON files** (`.json`) - Direct data with optional metadata
3. **Excel files** (`.xlsx`, `.xls`) - Tabular data

## Workflow

**IMPORTANT: You MUST ask the user questions at each step. Do NOT assume or decide for the user. Wait for their answers before proceeding.**

### Step 1: Understand User Goal

**ASK the user these questions (do not skip, do not assume):**

1. **"What is your goal with this RAG system?"**
   - Get a clear answer like: "query my support tickets", "search product documentation", "build a FAQ chatbot"

2. **"Who will use this?"**
   - Internal team / Customers / Public / Single user

3. **"What kind of queries will they ask?"**
   - Short questions / Detailed searches / Conversational

**Do NOT proceed until you have clear answers to ALL questions above.**

### Step 2: Identify Input Data

Ask user:
1. **Where is your data?** (file path or database connection)
2. **What format?** - SQL dump (`.sql`), JSON (`.json`), Excel (`.xlsx`), or CSV (`.csv`)
3. **Can you show me 2-3 sample records?** - This helps understand structure

### Step 3: Prepare Data for RAG (Skip if Already Compatible)

**First, analyze the user's data:**
- Load and examine 2-3 sample records
- Check average text length
- Identify field structure

**Then ASK: "Is your data already in this format?"**

Show them the RAG format:
```json
[
  {
    "text": "Searchable text content here",
    "metadata": {
      "id": "record-123",
      "category": "support"
    }
  }
]
```

**Based on your analysis, RECOMMEND what the `text` field should contain:**
- "I see your data has these fields: [list]. I recommend using `[field]` as the searchable text because [reason]."
- "The metadata should include: [fields] to help identify results."

**Ask for confirmation:** "Does this look right? Should I include/exclude any fields?"

**If data needs conversion:**
1. Recommend which fields to use for `text` and `metadata`
2. Suggest a filename based on content: `support_tickets.json`, `product_catalog.json`, etc.
3. Create the file and save to `data/{filename}.json`
4. Set `DATA_FILE=filename.json` in `.env`

**If data is already compatible:**
- Set `DATA_FILE=your_data.json` in `.env`
- Proceed to Step 4

### Step 4: Chunking Strategy

**Analyze the data first, then RECOMMEND based on your findings.**

**Based on your data analysis, tell the user:**

1. **"Your data looks like [short Q&A / medium documents / long articles / mixed] (avg length: ~X chars)"**

2. **"I recommend: [Chunking Type] with [Size] chunks"**

   Explain your recommendation:
   | Chunking | Why I recommend it |
   |----------|-------------------|
   | **Sentence (NLTK)** | Your entries are short Q&A or conversational data |
   | **Recursive** | Your entries are longer documents with paragraphs |

   | Size | Why |
   |------|-----|
   | **200-400** | Your queries seem to need high recall (many results) |
   | **500-800** | Balanced approach for mixed queries |
   | **800-1000+** | Your queries need precise, detailed results |

3. **"Does this work for you, or would you prefer something different?"**

**Do NOT just ask "what chunking do you want" - make a recommendation first.**

### Step 5: Embedding Model

**RECOMMEND based on the user's data language and use case:**

**"Based on your [language/data type], I recommend: [Model]"**

| Model | Best For | Dimensions | Why I recommend it |
|-------|---------|------------|-------------------|
| **BAAI/bge-m3** | Multilingual (Japanese, Chinese, 100+ languages) | 1024 | Best benchmark, free |
| **intfloat/multilingual-e5-small** | Fast CPU inference, smaller data | 384 | Quick, lightweight |
| **sentence-transformers/all-MiniLM-L6-v2** | English only, fastest | 384 | Very fast for English |

**Vector dimensions are auto-detected** based on the model. If using a custom model, set `VECTOR_SIZE` in `.env` if known.

**If user hasn't specified, default to BAAI/bge-m3** (best overall).

**Explain:** "Embeddings convert text to vectors. Similar concepts end up close together in 'embedding space' - this is how searches find relevant results."
Embeddings convert text into mathematical vectors. Similar concepts end up close together in "embedding space". When you search, it finds the closest vectors to your query.

**Why BGE-M3 is recommended**:
- Best multilingual support (100+ languages)
- Top accuracy on MTEB benchmark
- Free, open source
- 1024 dimensions

**Available options**:

| Model | Type | Multilingual | Dimensions | Cost | Best For |
|-------|------|--------------|------------|------|----------|
| **BGE-M3** | Open source | Yes (100+) | 1024 | Free | Best overall, multilingual |
| **Qwen3-Embedding-8B** | Open source | Yes | 1024 | Free | Newer, good for Chinese/English |
| **Cohere** | API | Yes | 1024 | Paid | Fast, reliable |
| **text-embedding-3-small** | API | Yes | 1536 | Paid | Simple setup |

Ask user: "I'll use BGE-M3 for embeddings - best multilingual performance. Any preference?"

### Step 6: LLM Configuration

**ASK and RECOMMEND:**

1. **"Where is your LLM running?"**
   - LM Studio (local)
   - OpenAI API
   - Other/custom

2. **"What's your model name?"** (e.g., llama-3, qwen3.5-2b, gpt-4)

3. **RECOMMEND temperature based on use case:**

   **"For [QA/data Q&A / conversational / creative] queries, I recommend temperature [X]"**

   | Temperature | Best For | Effect |
   |-------------|----------|--------|
   | **0.1-0.3** | Data Q&A, factual answers | Precise, consistent |
   | **0.4-0.6** | Balanced, general use | Moderate variation |
   | **0.7+** | Creative writing, brainstorming | More random |

   **Default: 0.2 (precise)** for data Q&A unless user says otherwise.

**Wait for answers before proceeding.**
- Local (LM Studio) or Cloud (OpenAI/Custom)?
- Model name if using LM Studio

**Temperature parameter - explain this:**
```
Temperature controls how "creative" vs "precise" the LLM responses are.

- Temperature 0.0-0.3: Precise, factual, consistent (best for data Q&A)
- Temperature 0.4-0.7: Balanced (default)
- Temperature 0.8-1.0: Creative, varied, may hallucinate

For a RAG system answering questions about your data:
Recommend 0.1-0.3 for accurate, factual answers
```

Ask user: "What temperature level? (0.1-0.3 for precise, 0.7 for balanced, 0.9+ for creative)"

### Step 7: Setup Instructions

After user confirms all preferences:

**Give user these commands to run (one at a time):**

1. First command:
```
docker compose up -d --build
```

2. Wait for user to confirm it's done
3. Verify: `docker ps` (should show qdrant-rag and rag-api)
4. Then give second command:
```
docker exec -it rag-api python -m src.ingest
```

5. Wait for user to confirm ingestion is done
6. Verify: `curl http://localhost:8769/health`

**NEVER run these commands yourself.**

### Step 8: System Prompt (Customize if Needed)

Based on user's goal, create appropriate system prompt:

**For QA/Question Answering:**
```
You are a helpful assistant that answers questions based on the provided context.
Only answer based on the context provided. If you cannot find the answer, say so.
Be concise and accurate.
```

**For Semantic Search:**
```
You are a search assistant. Return the most relevant information from the context.
Focus on finding exact matches and related information.
```

**For Data Analysis:**
```
You are a data analyst assistant. Help analyze and explain the data provided.
When numbers or statistics are in the context, include them in your response.
```

Ask user: "Does this system prompt work for your use case, or would you like to customize it?"

## Output Structure

Create folder at user's specified path (default: `rag-system`):

```
rag-system/
├── data/
│   └── exported_data.json    # User's data
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── ingest.py
│   ├── rag.py
│   └── main.py
├── scripts/
│   └── convert_data.py
├── vectors/
│   └── qdrant-data/          # Docker Qdrant storage
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── uv.lock                    # uv lock file (auto-generated)
└── .env
```

## Quick Start (Complete)

```bash
# Give user these commands to run (one at a time):

# 1. Start Docker
docker compose up -d

# Wait for user to confirm, then verify:
docker ps

# 2. Install dependencies
uv venv && source .venv/bin/activate && uv pip install -r requirements.txt

# 3. Ingest data
uv run python -m src.ingest

# Wait for confirmation, then verify:
curl http://localhost:8769/health

# 4. Test the API:
curl -X POST http://localhost:8769/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Your question", "top_k": 5}'
```

**IMPORTANT: Always use `uv run python` for Python scripts, not bare `python`.**

## Configuration (.env template)

```bash
# LLM Configuration
LLM_TYPE=lm_studio
LLM_ENDPOINT=http://192.168.0.194:1234/v1
LLM_MODEL=llama-3
LLM_TEMPERATURE=0.2

# Embeddings
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=cpu

# Vector Database
QDRANT_URL=http://qdrant:6333
COLLECTION_NAME=rag_collection

# API Server
API_PORT=8769
```

## Data File Setup

Place your data in the `data/` folder:
- **Filename**: `exported_data.json`
- **Format**: Array of objects with `text` and `metadata` fields

```json
[
  {
    "text": "Your document content here",
    "metadata": {
      "source": "source_file",
      "id": 1
    }
  }
]
```

## Troubleshooting

**Docker Issues:**
- Check if containers are running: `docker ps`
- View logs: `docker compose logs -f`
- Restart: `docker compose restart`
- Rebuild: `docker compose up -d --build`

**Qdrant Connection:**
- Check if Qdrant is healthy: `curl http://localhost:6533/health`
- Check collections: `curl http://localhost:6533/collections`

**Ingestion Issues:**
- Verify data file exists: `ls -la data/*.json`
- Run ingestion directly: `source .venv/bin/activate && uv run python -m src.ingest`
- Check error output for missing packages or data format issues

**Cannot Connect to LM Studio:**
- On Windows, use `host.docker.internal` to access localhost
- Or run the RAG API locally instead of in Docker
- Check LM Studio is running and "Start Server" is clicked

**Common Issues:**
- "Module not found" → Run `uv pip install -r requirements.txt`
- "Data file not found" → Check `DATA_PATH` in `.env` matches your file location
- "Embedding model error" → Make sure `sentence-transformers` is installed

## Key Concepts Summary

1. **Long Commands**: ALWAYS give user the command to run - never run yourself

2. **Chunking**: 
   - Smaller = more recall, more noise
   - Larger = less recall, better precision
   - Analyze data first before recommending

3. **Embeddings**: BGE-M3 for best multilingual support

4. **uv**: Use `uv pip install -r requirements.txt` for fast dependency management (or Docker handles this automatically)

5. **Temperature**: Low (0.1-0.3) for precise, higher for creative

6. **Verification**: After each user command, verify the result before proceeding
