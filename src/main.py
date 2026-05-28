import os
import sys
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from src.config import settings

app = FastAPI(
    title="SQL RAG API",
    description="RAG system built from SQL/JSON/Excel data",
    version="1.0.0",
)


class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    question: str


class IngestResponse(BaseModel):
    message: str
    status: str


class HealthResponse(BaseModel):
    status: str
    vector_db: str
    embedding_model: str
    llm_model: str
    port: int


@app.get("/health", response_model=HealthResponse)
async def health_check():
    embedding_model = (
        settings.embedding_model
        if settings.embedding_device == "cuda"
        else settings.cpu_embedding_model
    )
    return HealthResponse(
        status="healthy",
        vector_db="qdrant-docker" if settings.qdrant_url else "qdrant-local",
        embedding_model=embedding_model,
        llm_model=settings.llm_model,
        port=settings.api_port,
    )


@app.post("/rag/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    try:
        from src.rag import rag_system
        result = rag_system.query(request.query, top_k=request.top_k)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error querying RAG system: {str(e)}. Make sure you've run ingestion first.",
        )


@app.post("/rag/search")
async def search_only(request: QueryRequest):
    try:
        from src.rag import rag_system
        results = rag_system.search(request.query, top_k=request.top_k)
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rag/ingest", response_model=IngestResponse)
async def reingest_data():
    try:
        from src.ingest import ingest
        ingest()
        return IngestResponse(message="Data successfully re-ingested", status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {
        "message": "SQL RAG API is running",
        "port": settings.api_port,
        "docs": f"http://localhost:{settings.api_port}/docs",
        "endpoints": {
            "POST /rag/query": "Query the RAG system (uses LLM)",
            "POST /rag/search": "Pure vector search (no LLM)",
            "POST /rag/ingest": "Re-ingest data",
            "GET /health": "Health check",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
