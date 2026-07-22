import json
import os
from functools import lru_cache
from upstash_redis import Redis
from langchain_openai import ChatOpenAI

# config defaults for history window
MAX_HISTORY_TURNS = int(os.getenv("MEMORY_MAX_TURNS", "20"))
SESSION_TTL_SECONDS = int(os.getenv("MEMORY_TTL_SECONDS", "86400"))


@lru_cache(maxsize=1)

def _get_client() -> Redis:
# grab shared upstash redis client
    return Redis.from_env()


def _session_key(session_id: str) -> str:
    return f"session:{session_id}:history"


def _summary_key(session_id: str) -> str:
    return f"session:{session_id}:summary"


def get_history(session_id: str) -> list[dict]:
# pull raw turn list from redis list
    raw_items = _get_client().lrange(_session_key(session_id), 0, -1)
    return [json.loads(item) for item in raw_items]


def get_summary(session_id: str) -> str:
# TODO: add fallback if redis connection drops
    summary = _get_client().get(_summary_key(session_id))
    return summary if summary else ""


def append_turn(session_id: str, role: str, content: str) -> None:
    key = _session_key(session_id)
    client = _get_client()
    
    client.rpush(key, json.dumps({"role": role, "content": content}))
    total_turns = client.llen(key)
    
# summarize older turns when sliding window fills up
    if total_turns > MAX_HISTORY_TURNS:
        turns_to_summarize = client.lrange(key, 0, (total_turns - MAX_HISTORY_TURNS) - 1)
        parsed_turns = [json.loads(t) for t in turns_to_summarize]
        _update_long_term_summary(session_id, parsed_turns)
        client.ltrim(key, -MAX_HISTORY_TURNS, -1)
        
    client.expire(key, SESSION_TTL_SECONDS)
    client.expire(_summary_key(session_id), SESSION_TTL_SECONDS)


def _update_long_term_summary(session_id: str, older_turns: list[dict]):
    client = _get_client()
    curr_sumary = get_summary(session_id)
    formatted_turns = "\n".join([f"{t['role']}: {t['content']}" for t in older_turns])
    
    prompt = (
        f"You are a memory condensation utility for FinBot, a banking customer service bot.\n"
        f"Current Summary: {curr_sumary}\n\n"
        f"New conversation turns to compress into the summary:\n{formatted_turns}\n\n"
        f"Generate a new, consolidated summary incorporating the vital points from the new turns. "
        f"Keep it concise, focusing on core complaints, account issues, status updates, or user preferences. "
        f"Do not lose historical ticket IDs or critical event details."
    )
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
    res = llm.invoke(prompt)
    new_summary = res.content if hasattr(res, "content") else str(res)
    client.set(_summary_key(session_id), new_summary)


def clear_session(session_id: str) -> None:
# purge chat logs and summary
    client = _get_client()
    client.delete(_session_key(session_id))
    client.delete(_summary_key(session_id))