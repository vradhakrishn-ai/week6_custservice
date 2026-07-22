from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

class BaseVectorStore(ABC):
    """Abstract Base Class defining a common interface for swappable Vector Store backends."""

    @abstractmethod
    def ingest_documents(self, documents: List[Document]) -> None:
        """Ingests a list of LangChain documents into the vector database."""
        pass

    @abstractmethod
    def get_retriever(self, k: int = 5, metadata_filter: Optional[Dict[str, Any]] = None) -> BaseRetriever:
        """Returns a standard LangChain BaseRetriever with support for metadata filtering."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Purges the underlying collection or index."""
        pass