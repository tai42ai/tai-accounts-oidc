"""Pure OAuth2/OIDC crypto helpers — no I/O, no Redis, no settings.

The ``state`` parameter is tamper-evident: ``{state_id}.{hmac_sha256(state_id)}``
keyed by the operator's ``state_key``. The verifier only accepts a state whose
HMAC recomputes under the key (constant-time), returning the bare ``state_id``
the server-side record is stored under. PKCE is S256, always. Keeping this
module free of I/O keeps every branch here unit-testable in isolation.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets


def new_state_id() -> str:
    """A fresh random id the server-side state record is keyed under."""
    return secrets.token_urlsafe(16)


def new_nonce() -> str:
    """A fresh OIDC ``nonce`` — the id_token replay binding."""
    return secrets.token_urlsafe(16)


def new_sso_code() -> str:
    """A fresh one-time SSO hand-back code (never a token in the URL)."""
    return secrets.token_urlsafe(32)


def new_browser_binding() -> str:
    """A fresh secret tying an authorize->callback round trip to one browser.

    Stored in the server-side state record and mirrored into an HttpOnly cookie at
    authorize; the callback redeems a state only when the cookie matches. This
    binds the flow to the user agent that began it, so a state minted in one
    browser cannot be redeemed in another (login-CSRF / session fixation).
    """
    return secrets.token_urlsafe(32)


def _sign(state_id: str, key: bytes) -> str:
    return hmac.new(key, state_id.encode(), hashlib.sha256).hexdigest()


def sign_state(state_id: str, key: bytes) -> str:
    """Return the tamper-evident ``state`` value ``{state_id}.{hmac}``."""
    return f"{state_id}.{_sign(state_id, key)}"


def verify_state(state: str, key: bytes) -> str | None:
    """Return the ``state_id`` iff ``state``'s HMAC recomputes under ``key``.

    Constant-time compare; a malformed or tampered value returns ``None`` so the
    caller answers with a generic error and a detailed server log.
    """
    state_id, _, mac = state.partition(".")
    if not state_id or not mac:
        return None
    expected = _sign(state_id, key)
    if not hmac.compare_digest(mac, expected):
        return None
    return state_id


def pkce_pair() -> tuple[str, str]:
    """Return an S256 ``(verifier, challenge)`` pair.

    The verifier is a high-entropy URL-safe string; the challenge is the
    base64url-unpadded SHA-256 of its ASCII bytes (the S256 method).
    """
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge
