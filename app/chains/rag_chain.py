from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableParallel

from app.llm import get_llm
from app.model import RetrievedChunk
from app.rag_pipeline import ANSWER_PROMPT, RETRIEVAL_CONFIDENCE_THRESHOLD, should_use_direct_answer
from app.rbac.filter import apply_role_based_rag_filter
from app.rag_vectorstore import get_dense_retriever
from app.rag_reranker import rerank
from app.logging_utils import get_logger

logger = get_logger("rag.chain")


def get_rag_lcel_chain() -> RunnableParallel:
    """Small LCEL wrapper for KB-first answering."""
    llm = get_llm().with_retry(stop_after_attempt=3)
    retriever = get_dense_retriever(k=4)

    def decide_answer_path(retrieval_data: dict) -> str:
        docs = retrieval_data.get("docs", [])
        question = retrieval_data.get("question", "")
        
        logger.info(f"[LCEL CHAIN - decide_answer_path] Evaluating {len(docs)} documents")
        
        if not docs:
            logger.warning("[LCEL CHAIN] No documents retrieved - unable to answer from KB")
            return None
        
        reranked = rerank(question, docs, top_n=4)
        if not reranked:
            logger.warning("[LCEL CHAIN] Reranking produced no results")
            return None
        
        top_doc, top_score = reranked[0]
        
        logger.info(f"[LCEL CHAIN] Top document score: {top_score:.4f} | Threshold: {RETRIEVAL_CONFIDENCE_THRESHOLD}")

        candidate_contexts = [
            RetrievedChunk(
                content=top_doc.page_content,
                source=top_doc.metadata.get("source", "unknown"),
                score=top_score,
            )
        ]

        if should_use_direct_answer(question, candidate_contexts):
            logger.info(f"[LCEL CHAIN] ✅ DIRECT KB MATCH - Returning answer from {top_doc.metadata.get('source', 'unknown')}")
            return top_doc.page_content

        if top_score >= RETRIEVAL_CONFIDENCE_THRESHOLD:
            logger.info(f"[LCEL CHAIN] ✅ HIGH CONFIDENCE - Direct retrieval from {top_doc.metadata.get('source', 'unknown')}")
            return top_doc.page_content

        logger.warning(f"[LCEL CHAIN] ⚠ LOW CONFIDENCE - Will use LLM synthesis")
        return None

    def llm_synthesis_path(retrieval_data: dict) -> str:
        docs = retrieval_data.get("docs", [])
        question = retrieval_data.get("question", "")
        
        logger.info(f"[LCEL CHAIN - llm_synthesis] Starting LLM synthesis with {len(docs)} documents")
        
        if not docs:
            logger.warning("[LCEL CHAIN] No documents for LLM synthesis")
            return "I don't have information on that topic in the knowledge base."
        
        context_block = "\n\n".join(
            f"[{d.metadata.get('source', 'unknown')}] {d.page_content}" for d in docs
        )
        
        logger.info(f"[LCEL CHAIN] Invoking LLM with context block ({len(context_block)} chars)")
        result = (ANSWER_PROMPT | llm).invoke({
            "context": context_block,
            "question": question
        })
        
        response = result.content if hasattr(result, "content") else str(result)
        logger.info(f"[LCEL CHAIN] LLM synthesis complete ({len(response)} chars)")
        
        return response

    retrieval_stage = RunnableLambda(lambda inputs: retriever.invoke(inputs["question"]))
    rbac_stage = RunnableLambda(lambda docs_and_vars: apply_role_based_rag_filter(
        docs_and_vars["docs"], 
        docs_and_vars["config"].get("metadata", {}).get("user_role", "l1_agent")
    ))

    def smart_answer(retrieval_data: dict) -> str:
        question = retrieval_data.get("question", "")
        docs = retrieval_data.get("docs", [])
        
        logger.info(f"\n[LCEL CHAIN - smart_answer] Processing: '{question[:60]}...'")
        logger.info(f"[LCEL CHAIN] Available documents: {len(docs)}")
        
        retrieval_data_with_q = {"docs": docs, "question": question}
        direct_answer = decide_answer_path(retrieval_data_with_q)
        
        if direct_answer is not None:
            logger.info(f"[LCEL CHAIN] ✅ Using direct answer (no LLM)")
            return direct_answer
        
        logger.warning(f"[LCEL CHAIN] 🤖 Falling back to LLM synthesis")
        return llm_synthesis_path(retrieval_data_with_q)

    full_chain = (
        RunnableParallel({
            "docs": retrieval_stage,
            "question": lambda x: x["question"],
            "config": RunnablePassthrough()
        })
        | rbac_stage
        | smart_answer
    )

    return full_chain