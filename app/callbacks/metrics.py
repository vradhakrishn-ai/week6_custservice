import time
import logging
from typing import Any, Dict, List
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

logger = logging.getLogger("securebank.callbacks.metrics")

class PerformanceMetricsCallbackHandler(BaseCallbackHandler):
    """Custom lifecycle monitor measuring precise execution timing and token efficiency metrics."""

    def __init__(self):
        self._start_times: Dict[str, float] = {}

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], *, run_id: Any, **kwargs: Any) -> None:
        self._start_times[str(run_id)] = time.perf_counter()

    def on_llm_end(self, response: LLMResult, *, run_id: Any, **kwargs: Any) -> None:
        run_key = str(run_id)
        if run_key in self._start_times:
            duration_ms = (time.perf_counter() - self._start_times[run_key]) * 1000.0
            token_usage = response.llm_output.get("token_usage", {}) if response.llm_output else {}
            
            logger.info(
                "LLM Generation Lifecycle Completed",
                extra={
                    "latency_ms": round(duration_ms, 2),
                    "prompt_tokens": token_usage.get("prompt_tokens", 0),
                    "completion_tokens": token_usage.get("completion_tokens", 0),
                    "total_tokens": token_usage.get("total_tokens", 0)
                }
            )
            del self._start_times[run_key]