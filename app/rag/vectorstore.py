import os
from .base_store import BaseVectorStore
from .store_implementations import ChromaStore, FAISSStore, PineconeStore
from langchain_core.retrievers import BaseRetriever

def get_vector_backend() -> BaseVectorStore:
    """Factory resolver supplying the active swappable VectorStore concrete layout."""
    backend_choice = os.getenv("VECTOR_BACKEND", "chroma").lower().strip()
    
    if backend_choice == "chroma":
        return ChromaStore()
    elif backend_choice == "faiss":
        return FAISSStore()
    elif backend_choice == "pinecone":
        return PineconeStore()
    else:
        raise ValueError(f"Unsupported VECTOR_BACKEND config configuration layout: {backend_choice}")

def get_dense_retriever(k: int = 5) -> BaseRetriever:
    """Maintains backward compatibility with your active pipeline routes."""
    return get_vector_backend().get_retriever(k=k)