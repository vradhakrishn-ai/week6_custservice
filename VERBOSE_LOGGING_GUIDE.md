# Verbose RAG Logging Guide

## Overview

Comprehensive verbose logging has been added to the RAG system to help debug and understand why the LLM is or isn't being called for knowledge base queries.

## Logging Stages

The RAG pipeline logs at each major stage:

### Stage 1: Query Initialization
```
[RAG PIPELINE START] Query: 'How long does it take to activate a newly issued debit card?'
  User Role: l1_agent
  Confidence Threshold: 0.7
```

### Stage 2: HyDE Retrieval
```
[STAGE 1] Initial HyDE Retrieval...
  ✓ Retrieved 5 documents from HyDE retriever
    [1] Source: retail_banking_faq.csv | Preview: How long does it take to activate...
    [2] Source: retail_banking_faq.csv | Preview: What is the daily withdrawal limit...
    ...
```

### Stage 3: Role-Based Access Control
```
[STAGE 2] Applying Role-Based Access Control Filter...
  ✓ 5 document(s) passed RBAC check
```

Or if documents are filtered:
```
[STAGE 2] Applying Role-Based Access Control Filter...
  ⚠ Filtered out 2 document(s) due to RBAC
  ✓ 3 document(s) passed RBAC check
```

### Stage 4: Cross-Encoder Reranking
```
[STAGE 3] Cross-Encoder Reranking...
  ✓ Reranked 4 document(s)
    [1] Score: 0.9234 | Source: retail_banking_faq.csv | Preview: Debit cards are active...
    [2] Score: 0.5432 | Source: faq_general.html | Preview: Card activation requires...
    [3] Score: 0.3891 | Source: savings_account_faq.html | Preview: Savings products...
    [4] Score: 0.2156 | Source: retail_banking_faq.csv | Preview: Credit card benefits...
```

### Stage 5: Confidence Decision Logic
```
[STAGE 4] Confidence-Based Decision Logic...
  Total contexts available: 4
  ✅ HIGH CONFIDENCE MATCH!
     Top Score: 0.9234 >= Threshold: 0.7
     Source: retail_banking_faq.csv
  → DECISION: DIRECT RETRIEVAL (no LLM synthesis)
```

Or for low confidence:
```
[STAGE 4] Confidence-Based Decision Logic...
  Total contexts available: 4
  ⚠ LOW CONFIDENCE MATCH
     Top Score: 0.6543 < Threshold: 0.7
     Source: savings_account_faq.html
  → DECISION: Use LLM SYNTHESIS (score below threshold)
  Passing 4 context(s) to LLM for synthesis...
  ✓ LLM generated response (342 chars)
```

### Final Summary
```
[RAG PIPELINE END]
  LLM Used: False
  Total Latency: 2345ms
  Citations: retail_banking_faq.csv
================================================================================
```

## Debug Logging Points

### 1. Reranker Logging
Shows cross-encoder scores for each document:
```
[RERANKER] Starting rerank process
  Query: 'How long does it take to activate a newly issued debit card?'
  Documents to score: 5
  Top N to return: 4
  ✓ CrossEncoder produced 5 scores
  Sorted scores (descending):
    [1] Score: 0.9234 | retail_banking_faq.csv | Debit cards are active...
    [2] Score: 0.5432 | faq_general.html | Card activation requires...
    ...
  ✓ Reranking complete. Returning top 4 documents
```

### 2. RBAC Filter Logging
Shows which documents pass/fail RBAC checks:
```
[RBAC FILTER] Applying role-based filter for user_role: 'l1_agent'
[RBAC FILTER] Total documents before filtering: 5
[RBAC FILTER] Allowed doc types for 'l1_agent': ['faq', 'sop']
  ✓ [1] PASS: retail_banking_faq.csv (type: faq)
  ✓ [2] PASS: faq_general.html (type: faq)
  ✗ [3] FILTER OUT: confidential_memo.txt (type: internal) - not in allowed types
  ✓ [4] PASS: savings_account_faq.html (type: faq)
  ✗ [5] FILTER OUT: executive_summary.pdf (type: executive) - not in allowed types
[RBAC FILTER] Documents after filtering: 3 (removed: 2)
```

### 3. LCEL Chain Logging
Shows the decision path in the composed chain:
```
[LCEL CHAIN - smart_answer] Processing: 'How long does it take to activate a newly iss...'
[LCEL CHAIN] Available documents: 4
[LCEL CHAIN - decide_answer_path] Evaluating 4 documents
[RERANKER] Starting rerank process...
[LCEL CHAIN] Top document score: 0.9234 | Threshold: 0.7
[LCEL CHAIN] ✅ HIGH CONFIDENCE - Direct retrieval from retail_banking_faq.csv
[LCEL CHAIN] ✅ Using direct answer (no LLM)
```

## How to Enable Verbose Logging

### Option 1: Environment Variable
```bash
export LOG_LEVEL=DEBUG
python your_script.py
```

### Option 2: In Python Code
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Option 3: Configure Specific Logger
```python
import logging
logger = logging.getLogger("rag.pipeline")
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
```

## Troubleshooting: Why is LLM Still Being Called?

### Check 1: Low Confidence Score
Look for:
```
⚠ LOW CONFIDENCE MATCH
   Top Score: 0.6543 < Threshold: 0.7
```
**Solution**: Lower the threshold or improve document retrieval quality

### Check 2: Documents Filtered by RBAC
Look for:
```
⚠ Filtered out 3 document(s) due to RBAC
```
**Solution**: Check user role permissions in `config/roles.yaml`

### Check 3: No Documents Retrieved
Look for:
```
⚠ NO DOCUMENTS RETRIEVED - Cannot answer from knowledge base
```
**Solution**: Check if knowledge base is loaded properly or query needs reformulation

### Check 4: Reranking Issues
Look for CrossEncoder scores:
```
[1] Score: 0.4234 | ...
[2] Score: 0.3891 | ...
```
If all scores are low, documents may not be relevant to the query.

## Performance Metrics in Logs

The logs include latency information:
```
Total Latency: 2345ms
```

This shows:
- Direct retrieval is typically **50-500ms**
- LLM synthesis is typically **1000-3000ms**

Use this to identify performance bottlenecks.

## Log Levels

- `INFO`: Normal operation, decision paths
- `WARNING`: Subthreshold scores, RBAC filtering, fallback to LLM
- `ERROR`: Query failures, retriever errors (if any)

## Common Log Patterns

### Expected Pattern (Direct Retrieval)
```
✓ Retrieved 5 documents from HyDE retriever
✓ 5 document(s) passed RBAC check
✓ Reranked 4 document(s)
✅ HIGH CONFIDENCE MATCH!
   Top Score: 0.92 >= Threshold: 0.7
→ DECISION: DIRECT RETRIEVAL (no LLM synthesis)
LLM Used: False
```

### Expected Pattern (LLM Synthesis)
```
✓ Retrieved 5 documents from HyDE retriever
✓ 5 document(s) passed RBAC check
✓ Reranked 4 document(s)
⚠ LOW CONFIDENCE MATCH
   Top Score: 0.65 < Threshold: 0.7
→ DECISION: Use LLM SYNTHESIS (score below threshold)
✓ LLM generated response (342 chars)
LLM Used: True
```

## Files with Verbose Logging

1. **[app/rag_pipeline.py](../app/rag_pipeline.py)** - Main RAG pipeline (5 stages)
2. **[app/rag_reranker.py](../app/rag_reranker.py)** - Cross-encoder scoring
3. **[app/rbac/filter.py](../app/rbac/filter.py)** - Role-based filtering
4. **[app/chains/rag_chain.py](../app/chains/rag_chain.py)** - LCEL chain routing
5. **[app/rag_query_transform.py](../app/rag_query_transform.py)** - Query transformation

## Demo Script

Run the demo to see verbose logging in action:
```bash
cd /home/kasm-user/Documents/week8_project_v1
python demo_retrieval_confidence.py
```

This will show the full logging output for test queries.
