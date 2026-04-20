from __future__ import annotations

import os
from typing import Any
from dotenv import load_dotenv

load_dotenv()

try:
    from langfuse import observe, get_client
    from langfuse.client import Langfuse
    
    class _LangfuseContextShim:
        def __init__(self):
            self._current_span = None

        def update_current_trace(self, **kwargs: Any) -> None:
            client = get_client()
            if client:
                client.update_current_trace(**kwargs)

        def update_current_observation(self, **kwargs: Any) -> None:
            client = get_client()
            if client:
                try:
                    client.update_current_span(**kwargs)
                except Exception:
                    try:
                        client.update_current_generation(**kwargs)
                    except Exception:
                        pass

        def score(self, **kwargs: Any) -> None:
            client = get_client()
            if client:
                client.score_current_trace(**kwargs)

        def flush(self) -> None:
            client = get_client()
            if client:
                client.flush()

    langfuse_context = _LangfuseContextShim()

except Exception:  # pragma: no cover
    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func
        return decorator
    
    class _EmptyShim:
        def update_current_trace(self, **kwargs: Any) -> None: pass
        def update_current_observation(self, **kwargs: Any) -> None: pass
        def score(self, **kwargs: Any) -> None: pass
        def flush(self) -> None: pass

    langfuse_context = _EmptyShim()

    class _DummyContext:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_observation(self, **kwargs: Any) -> None:
            return None

        def score(self, **kwargs: Any) -> None:
            return None

    langfuse_context = _DummyContext()

def tracing_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))
