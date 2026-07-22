from app.prompts.semantic_selector import choose_prompt_slice
from app.prompts.prompt_manager import select_prompt_variant


def build_retrieval_payload(query: str) -> dict:
    selector = choose_prompt_slice(query)
    return {
        "query": query,
        "mode": "kb" if selector["slot"] == "kb" else "llm",
        "prompt_variant": select_prompt_variant(query),
        "confidence": selector["confidence"],
    }
