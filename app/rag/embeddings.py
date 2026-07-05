import os

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")
HF_EMBEDDING_MODEL = os.getenv("HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


def get_embeddings() -> Embeddings:
    """Factory for the configured embedding provider.

    Supports 'openai' and 'huggingface' out of the box based on the
    EMBEDDING_PROVIDER environment variable.
    """
    if EMBEDDING_PROVIDER == "openai":
        return OpenAIEmbeddings(model="text-embedding-3-small")
        
    elif EMBEDDING_PROVIDER == "huggingface":
        return HuggingFaceEmbeddings(
            model_name=HF_EMBEDDING_MODEL,
            encode_kwargs={"normalize_embeddings": True}  # Helpful for cosine similarity calculations
        )
        
    raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER}")