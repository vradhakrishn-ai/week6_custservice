# Customer Service & Complaint Resolution Assistant

This project is a LangChain-based banking support assistant for customer service and complaint resolution. It combines:

- a conversational agent with tool calling,
- retrieval-augmented generation (RAG) over banking documents,
- a FastAPI backend,
- a Streamlit frontend,
- structured logging and evaluation hooks.

The system is designed to handle banking-related support questions such as account inquiries, loan eligibility, card disputes, complaints, and policy lookups.

---

## What is currently implemented

### 1. Conversational agent
The app uses a LangChain-style tool-calling agent in [app/chain.py](app/chain.py) to manage multi-turn conversations and route requests through support tools.

### 2. Custom tools
The project includes several domain-specific tools in [app/tools.py](app/tools.py):

- Intent classification and routing
- Sentiment analysis
- Complaint handling
- Escalation handling

### 3. Prompting and persona setup
Prompting is implemented in [app/prompts.py](app/prompts.py) with:

- a banking assistant persona,
- system instructions,
- few-shot examples for common intents.

### 4. RAG pipeline
The project includes a retrieval pipeline in [app/rag](app/rag):

- document loading for PDF, DOCX, HTML, and CSV,
- chunking with recursive and semantic strategies,
- embedding support via OpenAI and Hugging Face,
- vector storage support via Chroma, FAISS, and Pinecone,
- hybrid retrieval with BM25 + dense search,
- cross-encoder reranking,
- answer generation with citations.

### 5. Backend API
The FastAPI app in [app/main.py](app/main.py) exposes:

- POST /chat
- POST /reset
- GET /health
- POST /retrieve
- POST /evaluate
- GET /sources
- DELETE /sources/{doc_id}

### 6. Frontend UI
A simple chat interface is implemented in [frontend/streamlit.py](frontend/streamlit.py).

### 7. Memory and caching
The app includes:

- Redis-backed session memory in [app/memory.py](app/memory.py)
- Redis-backed response caching in [app/cache.py](app/cache.py)

### 8. Evaluation harness
Evaluation is implemented in [eval/run_eval.py](eval/run_eval.py) and [eval/metrics.py](eval/metrics.py) for:

- retrieval quality,
- answer faithfulness,
- answer relevancy,
- end-to-end quality judgment.

### 9. Structured logging
The project uses structured JSON logging in [app/logging_utils.py](app/logging_utils.py).

---

## Project structure

```text
app/
  chain.py           Agent orchestration and tool usage
  llm.py             Shared LLM interface
  main.py            FastAPI endpoints
  memory.py          Session memory logic
  model.py           Pydantic schemas
  prompts.py         Prompt templates and few-shot examples
  tools.py           Domain tools for routing and support
  rag/               Retrieval pipeline modules
  logging_utils.py   Structured JSON logging

frontend/
  streamlit.py       Chat UI

eval/
  dataset.py         Evaluation dataset
  metrics.py         Evaluation scoring logic
  run_eval.py        Evaluation runner

data/
  knowledge_base/    Banking documents for RAG
  archive/           Additional sample files
```

---

## How to run the project

### 1. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
Create a `.env` file in the project root and set values such as:

```env
OPENAI_API_KEY="your_openai_key"
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=""
LANGSMITH_PROJECT="banking-ai-assistant"
UPSTASH_REDIS_REST_URL=""
UPSTASH_REDIS_REST_TOKEN=""
CHROMA_PERSIST_DIR="./data/chroma_db"
KNOWLEDGE_BASE_DIR="./data/knowledge_base"
```

### 4. Ingest the knowledge base

```bash
python -m app.rag.ingest
```

This loads the documents, chunks them, embeds them, and stores them in the configured vector store.

### 5. Start the backend

```bash
uvicorn app.main:app --reload
```

### 6. Start the frontend

In a separate terminal:

```bash
streamlit run frontend/streamlit.py
```

### 7. Run evaluation

```bash
python -m eval.run_eval
```

---

## How the main flow works

1. A user sends a message from the Streamlit UI.
2. The FastAPI backend receives the request at /chat.
3. The agent in [app/chain.py](app/chain.py) processes the turn.
4. The agent may call tools such as intent routing, sentiment analysis, or complaint handling.
5. If the query needs factual bank policy information, the RAG pipeline retrieves relevant documents and generates a grounded answer with citations.
6. The final response is returned to the frontend and stored in memory.

---