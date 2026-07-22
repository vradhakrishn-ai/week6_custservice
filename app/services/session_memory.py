from app import memory


def get_session_payload(session_id: str) -> dict:
    return memory.get_session(session_id)


def set_session_payload(session_id: str, payload: dict) -> None:
    memory.save_session(session_id, payload)
