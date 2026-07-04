import os
import time
import logging
from functools import lru_cache
from langchain_openai import ChatOpenAI
import openai

logger = logging.getLogger("securebank.llm")

@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model="gpt-4o-mini", 
        temperature=0.1, 
        max_retries=0
    )

def invoke_llm_with_retry(messages, max_attempts: int = 4, initial_backoff: float = 2.0):
    llm = get_llm()
    attempt = 0
    backoff = initial_backoff

    retryable_errors = (
        openai.APITimeoutError,
        openai.APIConnectionError,
        openai.RateLimitError,
        openai.InternalServerError,
    )

    while True:
        try:
            attempt += 1
            return llm.invoke(messages)
        except retryable_errors as e:
            if attempt >= max_attempts:
                logger.error(f"API invocation failed permanently after {max_attempts} attempts: {str(e)}")
                raise e
            
            logger.warning(
                f"Transient error encountered during LLM call (Attempt {attempt}/{max_attempts}). "
                f"Retrying in {backoff}s... Error: {type(e).__name__}"
            )
            time.sleep(backoff)
            backoff *= 2 