[🇺🇸 English](#english) | [🇯🇵 日本語](#日本語)

---

<a name="日本語"></a>
# Rag Builder

SQLダンプ、JSON、Excelファイルから完全なRAG（Retrieval Augmented Generation）システムを構築します。QdrantベクトルデータベースとFastAPIエンドポイントで検索結果を取得できます。

## 特徴

- **複数のデータフォーマット**: SQLダンプ、JSON、Excel、CSV
- **GPU/CPU自動検出**: GPUではBGE-M3、CPUではmultilingual-e5-smallを使用
- **ベクトル次元自動検出**: モデルに基づいて正しい埋め込み次元数を自動検出
- **柔軟なメタデータ**: データからすべてのフィールドを保持
- **Dockerまたはローカル**: Dockerですべてを実行、またはuvでローカル実行
- **QdrantベクトルDB**: コサイン類似度による高速セマンティック検索

---

## クイックスタート

```bash
# 1. リポジトリをクローンまたはコピー
git clone https://github.com/nakul-nsksystem/rag-builder.git
cd rag-builder

# 2. .envを編集して設定
cp .env.example .env
# .envを編集 - LLM URL、データファイルなどを設定

# 3. Dockerサービスを起動
docker compose up -d

# 4. Python依存関係をインストールしてデータを投入
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
uv run python -m src.ingest

# 5. APIを起動
uv run uvicorn src.main:app --host 0.0.0.0 --port 8769
```

API：http://localhost:8769/docs

---

## AIコーディングツールへのインストール

このスキルは**opencode**や**Claude Code**などのAIコーディングアシスタントで使用できます。

### opencode

`rag-builder`フォルダをopencodeスキルディレクトリにコピー：

```bash
cp -r rag-builder ~/.config/opencode/skills/rag-builder
```

 затем перезапустите opencode. スキルはRAGシステムの構築について質問すると自動的にロードされます。

**opencodeのファイル構造：**
```
~/.config/opencode/skills/rag-builder/
├── SKILL.md          # スキル指示書（必須）
├── src/              # ソースコード
├── scripts/          # ヘルパースクリプト
├── data/             # データフォルダ
├── requirements.txt  # Python依存関係
├── docker-compose.yml # Docker設定
├── Dockerfile        # Dockerイメージ
├── .env.example      # 設定テンプレート
└── README.md        # このファイル
```

### Claude Code

`rag-builder`フォルダをClaudeスキルディレクトリにコピー：

```bash
cp -r rag-builder ~/.claude/skills/rag-builder
```

またはプロジェクト固有のスキルには：

```bash
cp -r rag-builder /path/to/your/project/.claude/skills/rag-builder
```

**Claude Codeのファイル構造：**
```
~/.claude/skills/rag-builder/
├── SKILL.md          # スキル指示書（必須）
├── src/              # ソースコード
├── scripts/          # ヘルパースクリプト
├── data/             # データフォルダ
├── requirements.txt  # Python依存関係
├── docker-compose.yml # Docker設定
├── Dockerfile        # Dockerイメージ
├── .env.example      # 設定テンプレート
└── README.md        # このファイル
```

---

## 設定

`.env`ファイルを編集：

```bash
# LLM設定
LLM_BASE_URL=http://host.docker.internal:1234/v1
LLM_MODEL=llama-3
LLM_TEMPERATURE=0.2

# 埋め込み - GPU/CPUとベクトル次元を自動検出
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=cuda
CPU_EMBEDDING_MODEL=intfloat/multilingual-e5-small
VECTOR_SIZE=0  # 自動検出（カスタムモデルの場合は手動設定）

# チャンキング
CHUNK_SIZE=600
CHUNK_OVERLAP=100

# ベクトルデータベース
QDRANT_URL=http://qdrant:6333
COLLECTION_NAME=rag_collection

# データ - ファイルをdata/フォルダに配置
DATA_PATH=./data/exported_data.json

# APIサーバー
API_HOST=0.0.0.0
API_PORT=8769
```

### 埋め込みモデル

| モデル | 次元数 | 最適な用途 |
|-------|--------|-----------|
| BAAI/bge-m3 | 1024 | 多言語（日中英含む100以上） |
| intfloat/multilingual-e5-small | 384 | 高速CPU推論、小規模データ |
| sentence-transformers/all-MiniLM-L6-v2 | 384 | 英語のみ、最速 |

### ベクトル次元

ベクトル次元はモデルに基づいて自動検出されます：

| モデル | 次元数 |
|-------|--------|
| BAAI/bge-m3 | 1024 |
| BAAI/bge-large-zh-v1.5 | 1024 |
| BAAI/bge-base-zh-v1.5 | 768 |
| intfloat/multilingual-e5-small | 384 |
| intfloat/multilingual-e5-base | 768 |
| sentence-transformers/all-MiniLM-L6-v2 | 384 |
| sentence-transformers/all-mpnet-base-v2 | 768 |

---

## データフォーマット

### RAG形式（推奨）

```json
[
  {
    "text": "検索可能なテキストコンテンツ",
    "metadata": {
      "id": "record-123",
      "category": "support",
      "any_other_field": "value"
    }
  }
]
```

### 生テキスト配列（自動変換）

```json
["テキストエントリ1", "テキストエントリ2", "テキストエントリ3"]
```

### 生オブジェクト配列（自動変換）

```json
[
  {"question": "どうすればいい...", "answer": "你可以..."},
  {"question": "なぜ...", "answer": "Because..."}
]
```

---

## APIエンドポイント

| エンドポイント | メソッド | 説明 |
|----------|---------|-------------|
| `/rag/query` | POST | LLM合成でクエリ |
| `/rag/search` | POST | 純粋なベクトル検索（LLMなし） |
| `/rag/ingest` | POST | データの再投入 |
| `/health` | GET | ヘルスチェック |
| `/` | GET | API情報 |

### クエリの例

```bash
curl -X POST http://localhost:8769/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "あなたの質問", "top_k": 5}'
```

---

## Dockerコマンド

```bash
# サービス起動
docker compose up -d

# ログ表示
docker compose logs -f

# サービス停止
docker compose down

# 再構築（コード変更後）
docker compose up -d --build

# データ投入の手動実行
docker compose exec rag-api uv run python -m src.ingest
```

---

## ローカル開発

```bash
# venv作成
uv venv && source .venv/bin/activate

# 依存関係インストール
uv pip install -r requirements.txt

# データ投入
uv run python -m src.ingest

# API実行
uv run uvicorn src.main:app --reload
```

---

## プロジェクト構造

```
rag-builder/
├── src/
│   ├── __init__.py
│   ├── config.py       # GPU/CPU自動検出付き設定
│   ├── ingest.py       # データ投入パイプライン
│   ├── rag.py          # RAGクエリシステム
│   └── main.py         # FastAPIサーバー
├── scripts/
│   └── convert_data.py # データフォーマット変換
├── data/               # データファイル配置フォルダ
├── vectors/            # Qdrantストレージ（自動作成）
├── docker-compose.yml  # Dockerサービス
├── Dockerfile          # Dockerイメージ
├── requirements.txt    # Python依存関係
├── .env.example        # 設定テンプレート
├── SKILL.md            # AIアシスタントスキル指示書
└── README.md           # このファイル
```

---

## トラブルシューティング

### "Module not found"
```bash
uv pip install -r requirements.txt
```

### "Data file not found"
`DATA_PATH`がファイル場所と一致するか確認。

### "Embedding dimension mismatch"
`.env`の`VECTOR_SIZE`がモデルの次元数と一致するか確認、または`0`（自動）に設定。

### "Cannot connect to Qdrant"
```bash
curl http://localhost:6533/health
```
Docker使用の場合、コンテナが起動しているか確認：`docker ps`

### "Cannot connect to LLM"
- LM Studioが起動していて「Start Server」をクリックしているか確認
- `.env`の`LLM_BASE_URL`が正しいか確認

---

---

---

<a name="english"></a>
# Rag Builder

Build a complete RAG (Retrieval Augmented Generation) system from your SQL dumps, JSON, or Excel files. Creates a searchable vector database with Qdrant and a FastAPI endpoint for querying.

## Features

- **Multiple data formats**: SQL dumps, JSON, Excel, CSV
- **Auto GPU/CPU detection**: Uses BGE-M3 on GPU, multilingual-e5-small on CPU
- **Auto vector dimensions**: Detects correct embedding dimensions based on model
- **Flexible metadata**: Preserves all fields from your data
- **Docker or local**: Run everything in Docker or locally with uv
- **Qdrant vector DB**: Fast semantic search with cosine similarity

---

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

API: http://localhost:8769/docs

---

## Installation for AI Coding Tools

This skill can be used with **opencode** and **Claude Code** AI coding assistants.

### opencode

Copy the `rag-builder` folder to your opencode skills directory:

```bash
cp -r rag-builder ~/.config/opencode/skills/rag-builder
```

Then restart opencode. The skill will be automatically loaded when you ask about building RAG systems.

**opencode file structure:**
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

**Claude Code file structure:**
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
| intfloat/multilingual-e5-small | 384 | Fast CPU inference, smaller data |
| sentence-transformers/all-MiniLM-L6-v2 | 384 | English only, fastest |

### Vector Dimensions

Vector dimensions are auto-detected based on model:

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

