import os
import shutil
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_chroma import Chroma
from langchain_community.vectorstores import FAISS
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

from .base_store import BaseVectorStore
from .embeddings import get_embeddings

COLLECTION_NAME = "securebank_knowledge_base"

class ChromaStore(BaseVectorStore):
    def __init__(self):
        self.embeddings = get_embeddings()
        self.persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")

    def _get_client(self) -> Chroma:
        return Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=self.persist_dir,
        )

    def ingest_documents(self, documents: List[Document]) -> None:
        db = self._get_client()
        db.add_documents(documents)

    def get_retriever(self, k: int = 5, metadata_filter: Optional[Dict[str, Any]] = None) -> BaseRetriever:
        search_kwargs: Dict[str, Any] = {"k": k}
        if metadata_filter:
            search_kwargs["filter"] = metadata_filter
        return self._get_client().as_retriever(search_kwargs=search_kwargs)

    def clear(self) -> None:
        if os.path.exists(self.persist_dir):
            shutil.rmtree(self.persist_dir)
        os.makedirs(self.persist_dir, exist_ok=True)


class FAISSStore(BaseVectorStore):
    def __init__(self):
        self.embeddings = get_embeddings()
        self.persist_dir = os.getenv("FAISS_PERSIST_DIR", "./data/faiss_db")

    def ingest_documents(self, documents: List[Document]) -> None:
        db = FAISS.from_documents(documents, self.embeddings)
        db.save_local(self.persist_dir)

    def get_retriever(self, k: int = 5, metadata_filter: Optional[Dict[str, Any]] = None) -> BaseRetriever:
        if not os.path.exists(os.path.join(self.persist_dir, "index.faiss")):
            db = FAISS.from_documents([Document(page_content="initialization")], self.embeddings)
        else:
            db = FAISS.load_local(self.persist_dir, self.embeddings, allow_dangerous_deserialization=True)
            
        search_kwargs: Dict[str, Any] = {"k": k}
        if metadata_filter:
            search_kwargs["filter"] = metadata_filter
        return db.as_retriever(search_kwargs=search_kwargs)

    def clear(self) -> None:
        if os.path.exists(self.persist_dir):
            shutil.rmtree(self.persist_dir)
        os.makedirs(self.persist_dir, exist_ok=True)


class PineconeStore(BaseVectorStore):
    def __init__(self):
        self.embeddings = get_embeddings()
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", COLLECTION_NAME)
        
        if self.api_key:
            self.pc = Pinecone(api_key=self.api_key)
            # Provision serverless index if it doesn't exist
            if self.index_name not in [idx.name for idx in self.pc.list_indexes()]:
                self.pc.create_index(
                    name=self.index_name,
                    dimension=384 if "huggingface" in os.getenv("EMBEDDING_PROVIDER", "openai") else 1536,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1")
                )

    def ingest_documents(self, documents: List[Document]) -> None:
        PineconeVectorStore.from_documents(
            documents, self.embeddings, index_name=self.index_name, pinecone_api_key=self.api_key
        )

    def get_retriever(self, k: int = 5, metadata_filter: Optional[Dict[str, Any]] = None) -> BaseRetriever:
        db = PineconeVectorStore(index_name=self.index_name, embedding=self.embeddings, pinecone_api_key=self.api_key)
        search_kwargs: Dict[str, Any] = {"k": k}
        if metadata_filter:
            search_kwargs["filter"] = metadata_filter
        return db.as_retriever(search_kwargs=search_kwargs)

    def clear(self) -> None:
        if self.api_key and self.index_name in [idx.name for idx in self.pc.list_indexes()]:
            index = self.pc.Index(self.index_name)
            index.delete(delete_all=True)