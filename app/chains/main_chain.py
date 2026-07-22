from app.chain import chat


async def run_main_chain(session_id: str, message: str, user_role: str = "customer") -> tuple[str, bool]:
    return await chat(session_id=session_id, message=message, user_role=user_role)
