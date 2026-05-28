import json
import os
from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from tqdm import tqdm

from src.config import settings


def load_data(data_path: str):
    """Load data from JSON file. Handles both RAG format and raw text arrays."""
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Normalize to RAG format: [{text: ..., metadata: {...}}]
    normalized = []
    for i, item in enumerate(data):
        if isinstance(item, dict):
            # Already in RAG format
            text = item.get("text", "")
            metadata = item.get("metadata", {})
            # If no metadata, create from remaining fields
            if not metadata:
                metadata = {k: v for k, v in item.items() if k != "text"}
            normalized.append({"text": text, "metadata": metadata})
        elif isinstance(item, str):
            # Raw text array
            normalized.append({"text": item, "metadata": {"index": i}})
        else:
            raise ValueError(f"Unsupported data format at index {i}")

    return normalized


def chunk_data(data, chunk_size: int = 600, chunk_overlap: int = 100):
    """Split text into chunks while preserving metadata."""
    print(f"Chunking {len(data)} records...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
    )

    chunks = []
    for record in tqdm(data, desc="Processing records"):
        text = record["text"]
        metadata = record.get("metadata", {})

        if not text or len(text.strip()) == 0:
            continue

        record_chunks = text_splitter.split_text(text)

        for i, chunk_text in enumerate(record_chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata["_chunk_index"] = i
            chunk_metadata["_total_chunks"] = len(record_chunks)
            chunks.append({"text": chunk_text, "metadata": chunk_metadata})

    print(f"Created {len(chunks)} chunks from {len(data)} records")
    return chunks


def get_embedding_model():
    """Auto-detect GPU vs CPU and use appropriate model with correct dimensions."""
    if settings.embedding_device == "cuda":
        model = settings.embedding_model
    else:
        model = settings.cpu_embedding_model

    vector_size = settings.get_embedding_vector_size()

    print(f"Loading embedding model: {model} (device: {settings.embedding_device}, dims: {vector_size})")
    embeddings = HuggingFaceEmbeddings(
        model_name=model,
        model_kwargs={"device": settings.embedding_device},
        encode_kwargs={"normalize_embeddings": True},
    )
    return embeddings, vector_size


def store_in_qdrant(chunks, embeddings, vector_size):
    """Store chunks in Qdrant with flexible metadata."""
    print("Connecting to Qdrant...")

    if settings.qdrant_url:
        qdrant_client = QdrantClient(url=settings.qdrant_url, timeout=60)
    else:
        qdrant_client = QdrantClient(path=settings.qdrant_path or "./vectors/qdrant", timeout=60)

    collection_name = settings.collection_name

    # Delete existing collection if any
    try:
        qdrant_client.delete_collection(collection_name=collection_name)
        print(f"Deleted existing collection: {collection_name}")
    except Exception:
        pass

    # Create collection
    print(f"Creating collection with vector size {vector_size}...")
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )

    # Generate embeddings and store in batches
    print("Generating embeddings and storing...")
    batch_size = 100

    for i in tqdm(range(0, len(chunks), batch_size), desc="Embedding batches"):
        batch = chunks[i : i + batch_size]
        texts = [chunk["text"] for chunk in batch]

        vectors = embeddings.embed_documents(texts)

        points = []
        for j, (chunk, vector) in enumerate(zip(batch, vectors)):
            point_id = i + j
            # Store text + all metadata in payload
            payload = {"text": chunk["text"]}
            payload.update(chunk.get("metadata", {}))

            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector.tolist() if hasattr(vector, "tolist") else vector,
                    payload=payload,
                )
            )

        qdrant_client.upsert(collection_name=collection_name, points=points)

    print(f"Successfully stored {len(chunks)} chunks in Qdrant")


def ingest():
    """Main ingestion function."""
    print("=" * 50)
    print("Starting RAG ingestion process")
    print("=" * 50)

    data_path = settings.data_path
    print(f"Loading data from: {data_path}")

    data = load_data(data_path)
    chunks = chunk_data(data, settings.chunk_size, settings.chunk_overlap)
    embeddings, vector_size = get_embedding_model()
    store_in_qdrant(chunks, embeddings, vector_size)

    print("=" * 50)
    print("Ingestion complete!")
    print("=" * 50)


if __name__ == "__main__":
    ingest()
