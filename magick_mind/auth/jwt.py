"""Unverified JWT payload decoding.

The SDK never validates a token -- only the server can -- but it does read
claims the server put there (``sub`` for channel names, ``exp`` to schedule
rotation ahead of expiry, ``aud`` to learn whether the token may refresh).
"""

from __future__ import annotations

import base64
import json
from typing import Any, Optional

# Bifrost stamps refreshability into the audience: a supervised token is barred
# from the self-refresh route. A token with no audience predates the claim and
# is treated as self-managed, matching the server.
AUDIENCE_SELF_REFRESH = "end_user_self"
AUDIENCE_SUPERVISED = "end_user_supervised"


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


def jwt_audience(token: str) -> list[str]:
    """The ``aud`` claim as a list (the claim may be a string or an array)."""
    aud = decode_jwt_claims(token).get("aud")
    if isinstance(aud, str):
        return [aud]
    if isinstance(aud, list):
        return [a for a in aud if isinstance(a, str)]
    return []


def jwt_is_supervised(token: str) -> bool:
    """True when the token's audience marks it supervisor-managed."""
    return AUDIENCE_SUPERVISED in jwt_audience(token)
