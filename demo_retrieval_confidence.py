#!/usr/bin/env python3
"""
Demonstration of the Retrieval Confidence-Based Direct Answering System.

This script shows how the RAG system now:
1. Searches the knowledge base for answers
2. If confidence score >= 0.70, returns the answer DIRECTLY from the document (no LLM)
3. If confidence score < 0.70, uses the LLM to synthesize an answer

Example queries:
- "How long does it take to activate a newly issued debit card?" 
  → Will return directly from knowledge base (high confidence match)
- "What are the latest banking trends?"
  → Will use LLM synthesis (not found in knowledge base)
"""

import sys

sys.path.insert(0, "app")

from app.rag_pipeline import RAGPipeline, RETRIEVAL_CONFIDENCE_THRESHOLD
from app.llm import get_llm
from app.rag_loaders import load_knowledge_base
from app.rag_chunking import chunk_documents

print(f"🔍 Retrieval Confidence Threshold: {RETRIEVAL_CONFIDENCE_THRESHOLD}")
print(f"   Score >= {RETRIEVAL_CONFIDENCE_THRESHOLD} → Direct retrieval (NO LLM)")
print(f"   Score < {RETRIEVAL_CONFIDENCE_THRESHOLD} → LLM synthesis\n")

llm = get_llm()
pipeline = RAGPipeline(llm=llm, retrieve_k=5, rerank_top_n=4)

# Test queries
test_queries = [
    "How long does it take to activate a newly issued debit card?",
    "What is the interest rate on a basic savings account?",
    "What happens if I miss an EMI payment?",
]

print("=" * 80)
print("Testing Retrieval Confidence-Based Direct Answering")
print("=" * 80)

for query in test_queries:
    print(f"\n📝 Query: {query}")
    print("-" * 80)
    
    answer = pipeline.answer(query, user_role="l1_agent")
    
# Check if high-confidence direct retrieval was used
    if answer.contexts and answer.contexts[0].score >= RETRIEVAL_CONFIDENCE_THRESHOLD:
        print(f"✅ HIGH CONFIDENCE MATCH (score: {answer.contexts[0].score:.3f})")
        print(f"   Source: {answer.contexts[0].source}")
        print(f"   Status: RETURNED DIRECTLY FROM KNOWLEDGE BASE (no LLM used)")
    else:
        confidence = answer.contexts[0].score if answer.contexts else 0.0
        print(f"⚠️  LOW CONFIDENCE MATCH (score: {confidence:.3f})")
        print(f"   Status: LLM SYNTHESIS USED")
    
    print(f"\n📄 Answer:\n{answer.answer[:200]}...")
    print(f"\n🏷️  Sources: {', '.join(answer.citations)}")
    print("-" * 80)

print("\n✨ Retrieval Confidence System Demo Complete")
