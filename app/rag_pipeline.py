import re
import time
from typing import List

from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate

from app.logging_utils import get_logger, log_event
from app.model import RAGAnswer, RetrievedChunk
from app.rag_query_transform import get_hyde_retriever
from app.rag_reranker import rerank
from app.rbac.filter import apply_role_based_rag_filter

logger = get_logger("rag.pipeline")

RETRIEVAL_CONFIDENCE_THRESHOLD = 0.70

ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are FinBot, SecureBank India's AI banking assistant. Answer the "
        "customer's question using ONLY the context below. If the context "
        "does not contain the answer, say you don't have that information "
        "on file rather than guessing. Be concise and professional. After "
        "the answer, on a new line, cite the sources you used in the format "
        "'Sources: <file1>, <file2>'.\n\nContext:\n{context}"
    )),
    ("human", "{question}"),
])


DIRECT_ANSWER_TERMS = {
    "charge",
    "charges",
    "fee",
    "fees",
    "cost",
    "costs",
    "rate",
    "rates",
    "interest",
    "amount",
    "free",
    "limit",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "the",
    "to",
    "up",
    "what",
}


def _normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _token_overlap_score(query: str, content: str) -> float:
    query_tokens = {
        token for token in _normalize_text(query).split() if token and token not in STOPWORDS
    }
    content_tokens = {
        token for token in _normalize_text(content).split() if token and token not in STOPWORDS
    }

    if not query_tokens or not content_tokens:
        return 0.0

    overlap = query_tokens & content_tokens
    return len(overlap) / max(1, len(query_tokens | content_tokens))


def should_use_direct_answer(query: str, contexts: List[RetrievedChunk]) -> bool:
    if not contexts:
        return False

    top_doc = contexts[0]
    query_text = _normalize_text(query)
    content_text = _normalize_text(top_doc.content)

    if not query_text or not content_text:
        return False

    direct_intent = any(term in query_text for term in DIRECT_ANSWER_TERMS)
    answer_value_present = any(
        term in content_text
        for term in ("rs", "rupee", "gst", "free", "charge", "fee", "cost", "interest", "rate", "%")
    )
    numeric_overlap = bool(
        re.search(r"\d+(?:,\d{3})*(?:\.\d+)?", query_text)
        and re.search(r"\d+(?:,\d{3})*(?:\.\d+)?", content_text)
    )
    entity_overlap = _token_overlap_score(query, top_doc.content)
    recived = direct_intent and answer_value_present

    return recived and (entity_overlap >= 0.15 or numeric_overlap)


class RAGPipeline:
    def __init__(self, llm: BaseLanguageModel, retrieve_k: int = 5, rerank_top_n: int = 4):
        self._llm = llm
        self._retrieve_k = retrieve_k
        self._rerank_top_n = rerank_top_n
        
        self._retriever = get_hyde_retriever(llm, k=retrieve_k)
        self._chain = ANSWER_PROMPT | self._llm

    def answer(self, query: str, user_role: str = "l1_agent") -> RAGAnswer:
        """Main path for KB-first answering with a small LLM fallback."""
        start = time.monotonic()
        logger.info(f"\n{'='*80}")
        logger.info(f"[RAG PIPELINE START] Query: '{query}'")
        logger.info(f"  User Role: {user_role}")
        logger.info(f"  Confidence Threshold: {RETRIEVAL_CONFIDENCE_THRESHOLD}")
        logger.info(f"{'='*80}")
        
        logger.info("[STAGE 1] Initial HyDE Retrieval...")
        docs = self._retriever.invoke(query)
        logger.info(f"  ✓ Retrieved {len(docs)} documents from HyDE retriever")
        for idx, doc in enumerate(docs):
            source = doc.metadata.get("source", "unknown")
            preview = doc.page_content[:100].replace('\n', ' ')
            logger.info(f"    [{idx+1}] Source: {source} | Preview: {preview}...")
        
        logger.info("[STAGE 2] Applying Role-Based Access Control Filter...")
        allowed_docs = apply_role_based_rag_filter(docs, user_role)
        filtered_out = len(docs) - len(allowed_docs)
        if filtered_out > 0:
            logger.warning(f"  ⚠ Filtered out {filtered_out} document(s) due to RBAC")

        cnt = len(allowed_docs)
        logger.info(f"  ✓ {cnt} document(s) passed RBAC check")

        logger.info("[STAGE 3] Cross-Encoder Reranking...")
        reranked = rerank(query, allowed_docs, top_n=self._rerank_top_n)
        logger.info(f"  ✓ Reranked {len(reranked)} document(s)")
        for idx, (doc, score) in enumerate(reranked):
            source = doc.metadata.get("source", "unknown")
            preview = doc.page_content[:80].replace('\n', ' ')
            logger.info(f"    [{idx+1}] Score: {score:.4f} | Source: {source} | Preview: {preview}...")

        contexts = [
            RetrievedChunk(
                content=doc.page_content, 
                source=doc.metadata.get("source", "unknown"), 
                score=score
            )
            for doc, score in reranked
        ]
        citations = sorted({c.source for c in contexts})

        logger.info("[STAGE 4] Confidence-Based Decision Logic...")
        logger.info(f"  Total contexts available: {len(contexts)}")
        
        answer_text = None
        used_llm = False
        
        if not contexts:
            logger.warning("  ⚠ NO DOCUMENTS RETRIEVED - Cannot answer from knowledge base")
            logger.info("  → DECISION: Use LLM (no retrieval results)")
            used_llm = True
            context_block = ""
            result = self._chain.invoke({"context": "No knowledge base documents found.", "question": query})
            answer_text = result.content if hasattr(result, "content") else str(result)
        elif should_use_direct_answer(query, contexts):
            top_doc = contexts[0]
            logger.info(f"  ✅ DIRECT KB MATCH!")
            logger.info(f"     Top Score: {top_doc.score:.4f}")
            logger.info(f"     Source: {top_doc.source}")
            logger.info(f"  → DECISION: DIRECT RETRIEVAL (no LLM synthesis)")
            answer_text = top_doc.content
            log_event(
                logger,
                "rag direct retrieval - direct kb match",
                query=query,
                user_role=user_role,
                retrieved_count=len(docs),
                allowed_count=len(allowed_docs),
                reranked_count=len(reranked),
                top_score=top_doc.score,
                source=top_doc.source,
                latency_ms=round((time.monotonic() - start) * 1000, 1),
            )
        elif contexts[0].score >= RETRIEVAL_CONFIDENCE_THRESHOLD:
            top_doc = contexts[0]
            logger.info(f"  ✅ HIGH CONFIDENCE MATCH!")
            logger.info(f"     Top Score: {top_doc.score:.4f} >= Threshold: {RETRIEVAL_CONFIDENCE_THRESHOLD}")
            logger.info(f"     Source: {top_doc.source}")
            logger.info(f"  → DECISION: DIRECT RETRIEVAL (no LLM synthesis)")
            answer_text = top_doc.content
            log_event(
                logger,
                "rag direct retrieval - high confidence match",
                query=query,
                user_role=user_role,
                retrieved_count=len(docs),
                allowed_count=len(allowed_docs),
                reranked_count=len(reranked),
                top_score=top_doc.score,
                source=top_doc.source,
                latency_ms=round((time.monotonic() - start) * 1000, 1),
            )
        else:
            top_doc = contexts[0]
            logger.warning(f"  ⚠ LOW CONFIDENCE MATCH")
            logger.warning(f"     Top Score: {top_doc.score:.4f} < Threshold: {RETRIEVAL_CONFIDENCE_THRESHOLD}")
            logger.warning(f"     Source: {top_doc.source}")
            logger.warning(f"  → DECISION: Use LLM SYNTHESIS (score below threshold)")
            used_llm = True
            context_block = "\n\n".join(
                f"[{c.source}] {c.content}" for c in contexts
            )
            logger.info(f"  Passing {len(contexts)} context(s) to LLM for synthesis...")
            result = self._chain.invoke({"context": context_block, "question": query})
            answer_text = result.content if hasattr(result, "content") else str(result)
            logger.info(f"  ✓ LLM generated response ({len(answer_text)} chars)")
            
            log_event(
                logger,
                "rag llm synthesis - low confidence retrieval",
                query=query,
                user_role=user_role,
                retrieved_count=len(docs),
                allowed_count=len(allowed_docs),
                reranked_count=len(reranked),
                top_score=top_doc.score,
                confidence_threshold=RETRIEVAL_CONFIDENCE_THRESHOLD,
                sources=citations,
                latency_ms=round((time.monotonic() - start) * 1000, 1),
            )

        elapsed_ms = round((time.monotonic() - start) * 1000, 1)
        logger.info(f"\n[RAG PIPELINE END]")
        logger.info(f"  LLM Used: {used_llm}")
        logger.info(f"  Total Latency: {elapsed_ms}ms")
        logger.info(f"  Citations: {', '.join(citations) if citations else 'None'}")
        logger.info(f"{'='*80}\n")

        return RAGAnswer(answer=answer_text, citations=citations, contexts=contexts)