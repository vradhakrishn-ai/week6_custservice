"""Ingestion CLI: loads the knowledge base, chunks it, embeds it, and
upserts it into the persistent Chroma collection.

Usage: python -m app.rag_ingest
Idempotent: clears the existing collection before re-ingesting, so it's
safe to re-run after the source documents change.
"""
import os

from dotenv import load_dotenv

load_dotenv()

from app.logging_utils import get_logger, log_event
from app.rag_chunking import chunk_documents
from app.rag_loaders import load_knowledge_base
from app.rag_vectorstore import get_vector_backend

logger = get_logger("rag.ingest")


def _knowledge_base_dir() -> str:
    return os.getenv("KNOWLEDGE_BASE_DIR", "./data/knowledge_base")


def run_ingest() -> int:
    kb_dir = _knowledge_base_dir()
    log_event(logger, "loading knowledge base", directory=kb_dir)
    documents = load_knowledge_base(kb_dir)
    log_event(logger, "loaded documents", count=len(documents))

    chunks = chunk_documents(documents)
    log_event(logger, "chunked documents", chunk_count=len(chunks))

    vector_backend = get_vector_backend()
    vector_backend.clear()
    log_event(logger, "cleared existing data collection index layer")
    
    vector_backend.ingest_documents(chunks)
    log_event(logger, "ingested chunks into configured vector store", count=len(chunks))
    return len(chunks)

if __name__ == "__main__":
    run_ingest()
