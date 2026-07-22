from functools import wraps
import time


def retry(times: int = 2, delay: float = 0.1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:  # pragma: no cover - simple fallback
                    last_error = exc
                    if attempt < times - 1:
                        time.sleep(delay)
            raise last_error

        return wrapper

    return decorator
