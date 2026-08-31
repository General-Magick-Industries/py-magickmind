"""Unverified JWT payload decoding.

The SDK never validates a token -- only the server can -- but it does read
claims the server put there (``sub`` for channel names, ``exp`` to schedule
rotation ahead of expiry).
"""

from __future__ import annotations

import base64
import json
from typing import Any, Optional


def decode_jwt_claims(token: str) -> dict[str, Any]:
    """Return the payload segment of ``token`` as a dict, or ``{}`` if it is not
    a structurally valid JWT. The signature is never checked."""
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return {}
        payload_b64 = parts[1]
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def jwt_subject(token: str) -> Optional[str]:
    """The ``sub`` claim, or None when absent or not a string."""
    sub = decode_jwt_claims(token).get("sub")
    return sub if isinstance(sub, str) else None


def jwt_expiry(token: str) -> Optional[float]:
    """The ``exp`` claim as a unix timestamp, or None when absent or malformed."""
    exp = decode_jwt_claims(token).get("exp")
    if isinstance(exp, bool) or not isinstance(exp, (int, float)):
        return None
    return float(exp)
