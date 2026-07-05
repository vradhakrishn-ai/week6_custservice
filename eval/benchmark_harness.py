import os
import time
import numpy as np
from typing import List, Dict, Any
from langchain_core.documents import Document
from app.rag.vectorstore import BaseVectorStore
from app.rag.store_implementations import ChromaStore, FAISSStore, PineconeStore

def get_directory_size(directory: str) -> float:
    """Returns directory footprint size in Megabytes (MB)."""
    if not os.path.exists(directory):
        return 0.0
    total_size = 0
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return round(total_size / (1024 * 1024), 2)


def run_store_benchmark(store: BaseVectorStore, name: str, test_docs: List[Document], eval_queries: List[Dict[str, Any]]) -> Dict[str, Any]:
    print(f"Starting execution metrics profiling cycle for backend: {name}...")
    store.clear()
    
    # 1. Measure Ingestion Throughput Timing
    start_ingest = time.perf_counter()
    store.ingest_documents(test_docs)
    ingest_duration = time.perf_counter() - start_ingest
    
    # 2. Extract Footprint Space
    storage_footprint = "Cloud Managed"
    if name == "Chroma":
        storage_footprint = f"{get_directory_size(os.getenv('CHROMA_PERSIST_DIR', './data/chroma_db'))} MB"
    elif name == "FAISS":
        storage_footprint = f"{get_directory_size(os.getenv('FAISS_PERSIST_DIR', './data/faiss_db'))} MB"
        
    # 3. Assess Latency and Ground Truth Recall Precision
    retriever = store.get_retriever(k=5)
    latencies = []
    recall_scores = []
    
    for item in eval_queries:
        query = item["query"]
        expected_ids = item["expected_chunk_ids"]
        
        start_query = time.perf_counter()
        results = retriever.invoke(query)
        latency = time.perf_counter() - start_query
        latencies.append(latency)
        
        # Calculate Recall@5 against tagged ground-truth documents
        retrieved_ids = [doc.metadata.get("chunk_id") for doc in results]
        matched = sum(1 for e_id in expected_ids if e_id in retrieved_ids)
        recall_scores.append(matched / len(expected_ids) if expected_ids else 0.0)
        
    p50_latency = round(float(np.percentile(latencies, 50)) * 1000, 2)
    p95_latency = round(float(np.percentile(latencies, 95)) * 1000, 2)
    avg_recall = round(float(np.mean(recall_scores)) * 100, 2)
    
    return {
        "Backend": name,
        "Ingestion Time (s)": round(ingest_duration, 2),
        "p50 Latency (ms)": p50_latency,
        "p95 Latency (ms)": p95_latency,
        "Top-5 Recall (%)": avg_recall,
        "Storage Footprint": storage_footprint
    }

if __name__ == "__main__":
    # Sample Mock Documents for Benchmark Harness Running Execution
    sample_docs = [
        Document(page_content=f"SecureBank policy rule footprint text reference section index {i}.", metadata={"chunk_id": f"policy::recursive::{i}", "category": "banking_faq"})
        for i in range(100)
    ]
    
    # Target Evaluation Queries paired with Ground Truth Expectation keys
    queries = [
        {"query": "SecureBank policy rule footprint text reference section index 42", "expected_chunk_ids": ["policy::recursive::42"]},
        {"query": "banking policies overview index 87", "expected_chunk_ids": ["policy::recursive::87"]}
    ]
    
    backends = [
        (ChromaStore(), "Chroma"),
        (FAISSStore(), "FAISS")
    ]
    
    if os.getenv("PINECONE_API_KEY"):
        backends.append((PineconeStore(), "Pinecone"))
        
    results = []
    for store_obj, label in backends:
        metrics = run_store_benchmark(store_obj, label, sample_docs, queries)
        results.append(metrics)
        
    print("\n=== SYSTEM PERFORMANCE BENCHMARK REPORT ===")
    print(f"{'Backend':<12} | {'Ingest (s)':<10} | {'p50 (ms)':<8} | {'p95 (ms)':<8} | {'Recall':<8} | {'Size':<10}")
    print("-" * 68)
    for r in results:
        print(f"{r['Backend']:<12} | {r['Ingestion Time (s)']:<10} | {r['p50 Latency (ms)']:<8} | {r['p95 Latency (ms)']:<8} | {r['Top-5 Recall (%)']}%   | {r['Storage Footprint']:<10}")