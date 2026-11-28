import math
from typing import Any


def finite(x: Any, default: float = 0.0) -> float:
    """float(x), or `default` if it is NaN / inf / not a number.
    NaN is not valid JSON, so one stray NaN would turn a whole response into a 500."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    return v if math.isfinite(v) else default


def json_safe(obj: Any) -> Any:
    """Recursively make a response JSON-safe: numpy scalars -> Python, NaN/inf -> None."""
    if isinstance(obj, dict):
        return {str(k): json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_safe(v) for v in obj]
    if hasattr(obj, "item") and not isinstance(obj, (str, bytes)):
        try:
            obj = obj.item()
        except Exception:
            pass
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    return obj
