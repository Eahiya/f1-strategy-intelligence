"""
JSON Sanitizer for FastAPI - Universal type converter.

Converts ALL NumPy, pandas, and datetime types to Python native types
before JSON serialization, preventing TypeError in FastAPI responses.
"""
import numpy as np
import pandas as pd
from datetime import datetime, date
from typing import Any
import logging
import math

logger = logging.getLogger(__name__)


def sanitize_for_json(obj: Any) -> Any:
    """
    Recursively convert any non-JSON-serializable type to a Python native type.

    Handles:
    - dict         -> recursively sanitize keys and values
    - list/tuple/set -> list with sanitized elements
    - np.bool_     -> bool
    - np.integer   -> int
    - np.floating  -> float  (NaN/Inf → None)
    - np.str_      -> str
    - np.ndarray   -> list (recursed)
    - np.datetime64 / np.timedelta64 -> str / int
    - pd.Series    -> dict (recursed)
    - pd.DataFrame -> list of records (recursed)
    - datetime/date -> ISO-8601 str
    - str/int/float/bool/None -> returned as-is
    - anything else -> str(obj) fallback
    """

    # ── None ──────────────────────────────────────────────────────────────────
    if obj is None:
        return None

    # ── dict ──────────────────────────────────────────────────────────────────
    if isinstance(obj, dict):
        return {
            str(k): sanitize_for_json(v)
            for k, v in obj.items()
        }

    # ── list / tuple / set ────────────────────────────────────────────────────
    if isinstance(obj, (list, tuple, set)):
        return [sanitize_for_json(v) for v in obj]

    # ── NumPy bool ────────────────────────────────────────────────────────────
    if isinstance(obj, np.bool_):
        return bool(obj)

    # ── NumPy integers ────────────────────────────────────────────────────────
    if isinstance(obj, np.integer):
        return int(obj)

    # ── NumPy floats ──────────────────────────────────────────────────────────
    if isinstance(obj, np.floating):
        f = float(obj)
        if math.isnan(f) or math.isinf(f):
            return None
        return f

    # ── NumPy strings (np.str_ is the only numpy string type in NumPy ≥2) ────
    if isinstance(obj, np.str_):
        return str(obj)

    # ── NumPy arrays ──────────────────────────────────────────────────────────
    if isinstance(obj, np.ndarray):
        return sanitize_for_json(obj.tolist())

    # ── NumPy datetime64 ──────────────────────────────────────────────────────
    if isinstance(obj, np.datetime64):
        return str(obj)

    # ── NumPy timedelta64 ─────────────────────────────────────────────────────
    if isinstance(obj, np.timedelta64):
        try:
            return int(obj.astype("timedelta64[ms]").astype(int))
        except Exception:
            return str(obj)

    # ── pandas Series ─────────────────────────────────────────────────────────
    if isinstance(obj, pd.Series):
        return sanitize_for_json(obj.to_dict())

    # ── pandas DataFrame ──────────────────────────────────────────────────────
    if isinstance(obj, pd.DataFrame):
        return sanitize_for_json(obj.to_dict(orient="records"))

    # ── Python datetime / date ────────────────────────────────────────────────
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    # ── Native Python scalars (pass-through) ──────────────────────────────────
    if isinstance(obj, (str, int, float, bool)):
        # Guard against Python float NaN/Inf as well
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        return obj

    # ── Generic numpy scalar fallback ─────────────────────────────────────────
    if isinstance(obj, np.generic):
        return obj.item()

    # ── Objects with pandas-style .to_dict() ──────────────────────────────────
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        return sanitize_for_json(obj.to_dict())

    # ── Objects with numpy-style .tolist() ────────────────────────────────────
    if hasattr(obj, "tolist") and callable(obj.tolist):
        return sanitize_for_json(obj.tolist())

    # ── Final fallback ────────────────────────────────────────────────────────
    return str(obj)


def sanitize_response(data: Any, endpoint: str = "unknown") -> Any:
    """
    Sanitize response data with error logging.

    Raises HTTPException-friendly dict on failure so callers can re-raise properly.
    """
    try:
        sanitized = sanitize_for_json(data)
        return sanitized
    except Exception as e:
        logger.error(f"[sanitize_response] Error sanitizing {endpoint}: {e}", exc_info=True)
        raise RuntimeError(f"Serialization error in {endpoint}: {e}") from e


def debug_response_types(response: dict, label: str = "RESPONSE") -> None:
    """
    Print the top-level types of a response dict for debugging.
    Call this before returning from any endpoint.
    """
    print(f"\n── {label} TYPES ──")
    if isinstance(response, dict):
        for k, v in response.items():
            print(f"  {k}: {type(v).__name__}")
    else:
        print(f"  (not a dict) {type(response).__name__}")
    print("────────────────────\n")


# ── Convenience alias ─────────────────────────────────────────────────────────
def json_safe(data: Any, endpoint: str = "unknown") -> Any:
    """Sanitize and return data, wrapping non-dict in {'data': ...}."""
    sanitized = sanitize_response(data, endpoint)
    if isinstance(sanitized, dict):
        return sanitized
    return {"data": sanitized}
