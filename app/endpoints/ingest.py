from app.rag_ingest import ingest_documents


def run_ingestion() -> dict:
    ingest_documents()
    return {"status": "completed"}
