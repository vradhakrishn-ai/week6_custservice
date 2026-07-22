# Retrieval Confidence-Based Direct Answering

## Overview

The system now implements intelligent retrieval-based answering that avoids unnecessary LLM calls for questions found in the knowledge base.

## How It Works

### Processing Flow

```
User Query
    ↓
[1] Retrieve documents from knowledge base (HyDE retriever)
    ↓
[2] Apply role-based access controls
    ↓
[3] Rerank documents using cross-encoder
    ↓
[4] Check confidence score of top result
    ├─→ Score >= 0.70? → Return document DIRECTLY (no LLM) ✅
    └─→ Score < 0.70? → Pass to LLM for synthesis 🤖
```

## Confidence Threshold

**Default: 0.70** (configurable in `app/rag_pipeline.py`)

- **Score Range**: 0.0 to 1.0 (from cross-encoder model)
- **High Confidence (≥ 0.70)**: Direct document retrieval used
- **Low Confidence (< 0.70)**: LLM synthesis used

## Examples

### Direct Retrieval (No LLM)
```
Query: "How long does it take to activate a newly issued debit card?"

Knowledge Base has:
"Debit cards are active for online transactions immediately upon generating a 
PIN via the mobile application."

Confidence Score: 0.92 ✅
Result: DIRECT RETRIEVAL - Answer returned from document without LLM call
```

### LLM Synthesis
```
Query: "What are the latest trends in digital banking?"

Knowledge Base search:
- No exact match found
- Highest confidence score: 0.45 (below threshold)

Result: LLM SYNTHESIS - Question passed to LLM for generation
```

## Configuration

### Adjusting the Confidence Threshold

Edit `app/rag_pipeline.py`:

```python
# Increase threshold (more selective, more LLM calls)
RETRIEVAL_CONFIDENCE_THRESHOLD = 0.80  # Only very confident matches use direct retrieval

# Decrease threshold (less selective, fewer LLM calls)
RETRIEVAL_CONFIDENCE_THRESHOLD = 0.50  # More matches use direct retrieval
```

### Recommended Values

| Threshold | Use Case |
|-----------|----------|
| **0.50** | Aggressive cost reduction, accept more approximate answers |
| **0.70** | Balanced (default) - good accuracy with reduced LLM calls |
| **0.85** | High quality - prioritize LLM synthesis over direct retrieval |
| **1.00** | Always use LLM synthesis (disables direct retrieval) |

## Benefits

1. **Cost Reduction**: LLM calls only for queries NOT in knowledge base
2. **Faster Responses**: Direct retrieval is faster than LLM synthesis
3. **Consistency**: Answers from knowledge base are consistent/verified
4. **Accuracy**: LLM synthesis used strategically for complex queries

## Monitoring

Check logs for retrieval mode:

```
"rag direct retrieval - high confidence match" → Document returned directly
"rag llm synthesis - low confidence retrieval" → LLM was used for synthesis
```

## Knowledge Base

Current knowledge base includes:
- [data/knowledge_base/retail_banking.faq](../data/knowledge_base/retail_banking.faq)
- [data/knowledge_base/savings_account_faq.html](../data/knowledge_base/savings_account_faq.html)
- [data/knowledge_base/faq_general.html](../data/knowledge_base/faq_general.html)

To add new documents:
1. Place file in `data/knowledge_base/`
2. Restart the service (knowledge base is indexed at startup)
