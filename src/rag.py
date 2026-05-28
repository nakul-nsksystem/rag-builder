from typing import List, Dict, Any, Optional

from langchain_openai import ChatOpenAI
from qdrant_client import QdrantClient

from src.config import settings


class RAGSystem:
    def __init__(self):
        self.llm = ChatOpenAI(
            base_url=settings.llm_base_url,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            api_key="not-needed",
        )

        if settings.qdrant_url:
            self.qdrant_client = QdrantClient(url=settings.qdrant_url, timeout=60)
        else:
            self.qdrant_client = QdrantClient(path=settings.qdrant_path or "./vectors/qdrant", timeout=60)

        self.collection_name = settings.collection_name

    def _get_embeddings(self):
        """Get embedding model based on device."""
        from langchain_huggingface import HuggingFaceEmbeddings

        if settings.embedding_device == "cuda":
            model = settings.embedding_model
        else:
            model = settings.cpu_embedding_model

        return HuggingFaceEmbeddings(
            model_name=model,
            model_kwargs={"device": settings.embedding_device},
            encode_kwargs={"normalize_embeddings": True},
        )

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Pure vector search - returns raw results without LLM."""
        embeddings = self._get_embeddings()
        query_vector = embeddings.embed_query(query)

        search_results = self.qdrant_client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            with_payload=True,
        )

        results = []
        for result in search_results.points:
            payload = result.payload
            # Extract text and metadata (everything except text field)
            result_data = {
                "score": result.score,
                "text": payload.get("text", ""),
            }
            # Add all other fields as metadata
            for key, value in payload.items():
                if key != "text":
                    result_data[key] = value
            results.append(result_data)

        return results

    def query(self, user_query: str, top_k: int = 5) -> Dict[str, Any]:
        """Query with LLM synthesis."""
        search_results = self.search(user_query, top_k=top_k)

        if not search_results:
            return {
                "answer": "No relevant information found for your query.",
                "sources": [],
                "question": user_query,
            }

        # Format context from search results
        context_parts = []
        for i, r in enumerate(search_results):
            # Filter out internal fields
            metadata_str = ", ".join(
                f"{k}: {v}" for k, v in r.items() if k not in ["text", "score", "_chunk_index", "_total_chunks"]
            )
            context_parts.append(f"Case {i + 1}: {r.get('text', '')} [{metadata_str}]")

        context = "\n\n".join(context_parts)

        system_prompt = """You are a helpful assistant that answers questions based on the provided context.
Only answer based on the context provided. If you cannot find the answer, say so.
Be concise and accurate."""

        user_prompt = f"""Context:
{context}

Question: {user_query}

Answer the question based on the context above."""

        response = self.llm.invoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )

        # Format sources (exclude internal fields)
        sources = []
        for r in search_results:
            source = {k: v for k, v in r.items() if k not in ["_chunk_index", "_total_chunks"]}
            sources.append(source)

        return {
            "answer": response.content if hasattr(response, "content") else str(response),
            "sources": sources,
            "question": user_query,
        }


rag_system = RAGSystem()
