import os
from pathlib import Path

from pydantic_settings import BaseSettings


# Known embedding dimensions
EMBEDDING_DIMENSIONS = {
    "BAAI/bge-m3": 1024,
    "BAAI/bge-large-zh-v1.5": 1024,
    "BAAI/bge-base-zh-v1.5": 768,
    "intfloat/multilingual-e5-small": 384,
    "intfloat/multilingual-e5-base": 768,
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "sentence-transformers/all-mpnet-base-v2": 768,
}


def get_embedding_dimensions(model_name: str) -> int:
    """Get vector dimensions for known models, or auto-detect from config."""
    # Check known models
    for known_model, dims in EMBEDDING_DIMENSIONS.items():
        if known_model in model_name:
            return dims
    # Default fallback
    return 1024


class Settings(BaseSettings):
    # LLM Settings
    llm_base_url: str = "http://host.docker.internal:1234/v1"
    llm_model: str = "llama-3"
    llm_temperature: float = 0.2

    # Embeddings - auto-detects GPU vs CPU
    embedding_model: str = "BAAI/bge-m3"
    embedding_device: str = "cuda"
    cpu_embedding_model: str = "intfloat/multilingual-e5-small"

    # Vector size - auto-detected based on model if not set
    vector_size: int = 0

    # Chunking settings
    chunk_size: int = 600
    chunk_overlap: int = 100

    # Vector DB
    qdrant_url: str = "http://qdrant:6333"
    qdrant_path: str = "./vectors/qdrant"
    collection_name: str = "rag_collection"

    # Data
    data_path: str = "./data/exported_data.json"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8769

    def get_embedding_vector_size(self) -> int:
        """Get vector size, auto-detecting from model if not explicitly set."""
        if self.vector_size > 0:
            return self.vector_size
        if self.embedding_device == "cuda":
            return get_embedding_dimensions(self.embedding_model)
        return get_embedding_dimensions(self.cpu_embedding_model)

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
