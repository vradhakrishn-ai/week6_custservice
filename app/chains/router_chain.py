from app.prompts.prompt_manager import select_prompt_variant


def route_query(message: str) -> str:
    return select_prompt_variant(message)
