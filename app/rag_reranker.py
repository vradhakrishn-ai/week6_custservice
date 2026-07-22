from functools import lru_cache

from langchain_core.documents import Document
from sentence_transformers import CrossEncoder
from app.logging_utils import get_logger

logger = get_logger("rag.reranker")

MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


@lru_cache(maxsize=1)
def _get_model() -> CrossEncoder:
# cached cross encoder loader
    logger.info(f"[RERANKER] Loading CrossEncoder model: {MODEL_NAME}")
    model = CrossEncoder(MODEL_NAME)
    logger.info(f"[RERANKER] Model loaded successfully")
    return model


def rerank(query: str, documents: list[Document], top_n: int = 4) -> list[tuple[Document, float]]:
    if not documents:
        logger.warning("[RERANKER] No documents provided for reranking")
        return []
    
    logger.info(f"\n[RERANKER] Starting rerank process")
    logger.info(f"  Query: '{query}'")
    logger.info(f"  Documents to score: {len(documents)}")
    logger.info(f"  Top N to return: {top_n}")
    
    model = _get_model()
    pairs = [(query, doc.page_content) for doc in documents]
    scores = model.predict(pairs)
    
    logger.info(f"  ✓ CrossEncoder produced {len(scores)} scores")
    
    scored = sorted(zip(documents, scores), key=lambda pair: pair[1], reverse=True)
    
    logger.info(f"  Sorted scores (descending):")
    for idx, (doc, score) in enumerate(scored[:top_n]):
        source = doc.metadata.get("source", "unknown")
        preview = doc.page_content[:60].replace('\n', ' ')
        logger.info(f"    [{idx+1}] Score: {score:.4f} | {source} | {preview}...")
    
    result = [(doc, float(score)) for doc, score in scored[:top_n]]
    logger.info(f"  ✓ Reranking complete. Returning top {len(result)} documents\n")
    
    return result