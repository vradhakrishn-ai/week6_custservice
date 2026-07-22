try:
    from langchain_classic.retrievers.multi_query import MultiQueryRetriever
except ModuleNotFoundError:
    from langchain.retrievers.multi_query import MultiQueryRetriever

from langchain_core.language_models import BaseLanguageModel
from langchain_core.retrievers import BaseRetriever

from app.rag_hybrid_retriever import get_hybrid_retriever
from app.logging_utils import get_logger

logger = get_logger("rag.query_transform")


def get_multi_query_retriever(llm: BaseLanguageModel, k: int = 5) -> BaseRetriever:
    """Multi-query transform: LLM rephrases user question into variants,

    retrieves for each against hybrid (BM25 + dense) retriever, and
    deduplicates.
    """
    logger.info("[QUERY TRANSFORM] Initializing Multi-Query Retriever")
    retriever = MultiQueryRetriever.from_llm(
        retriever=get_hybrid_retriever(k=k),
        llm=llm,
    )
    logger.info(f"[QUERY TRANSFORM] Multi-Query Retriever configured (k={k})")
    return retriever


def get_hyde_retriever(llm: BaseLanguageModel, k: int = 5) -> BaseRetriever:
    """Compatibility wrapper used by the RAG pipeline with verbose logging."""
    logger.info(f"[HYDE RETRIEVER] Initializing HyDE retriever (k={k})")
    return get_multi_query_retriever(llm=llm, k=k)