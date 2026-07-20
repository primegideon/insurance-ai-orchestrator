"""
auth.py – FastAPI dependency for Supabase JWT bearer token verification.

Your Supabase project uses ES256 (elliptic-curve asymmetric signing).
Tokens are verified LOCALLY against the EC public key fetched once from
Supabase's JWKS endpoint at startup — zero network I/O on every request.

Startup flow  (called from main.py lifespan):
    init_jwks()  →  fetches /auth/v1/.well-known/jwks.json
                 →  builds a {kid: ECPublicKey} cache

Per-request flow  (Depends(verify_token)):
    1. HTTPBearer extracts the Bearer token from the Authorization header.
    2. jwt.get_unverified_header() reads the kid + alg fields.
    3. The matching public key is looked up from the in-memory cache.
    4. jwt.decode() verifies the signature and expiry — pure CPU, no I/O.
    5. Returns the decoded payload dict on success, raises HTTP 401 on any failure.
"""

import logging
import os
from typing import Optional

import jwt
import requests as http  # already in requirements; used only at startup
from jwt.algorithms import ECAlgorithm
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)

# Module-level key cache: maps kid → public key object
# Populated once by init_jwks() during application startup.
_jwks_cache: dict[str, object] = {}


# ---------------------------------------------------------------------------
# Startup helper
# ---------------------------------------------------------------------------

def init_jwks() -> None:
    """Fetch the Supabase JWKS and cache the public key(s).

    Must be called during application lifespan startup before any request
    can be authenticated.

    Raises:
        RuntimeError: If SUPABASE_URL is missing or the endpoint is unreachable.
    """
    global _jwks_cache

    supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    if not supabase_url:
        raise RuntimeError("SUPABASE_URL is not set — cannot fetch JWKS.")

    jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
    logger.info("Fetching JWKS from %s …", jwks_url)

    try:
        resp = http.get(jwks_url, timeout=10)
        resp.raise_for_status()
        keys = resp.json().get("keys", [])
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch JWKS from Supabase: {exc}") from exc

    if not keys:
        raise RuntimeError(f"JWKS response from {jwks_url} contained no keys.")

    _jwks_cache = {}
    for jwk in keys:
        kid = jwk.get("kid", "default")
        alg = jwk.get("alg", "ES256")
        if alg.startswith("EC") or alg == "ES256":
            public_key = ECAlgorithm.from_jwk(jwk)
        else:
            # Fallback — shouldn't happen for this project but be defensive
            logger.warning("Unsupported JWKS key alg %s for kid %s — skipping.", alg, kid)
            continue
        _jwks_cache[kid] = public_key
        logger.info("JWKS key cached — kid: %s  alg: %s", kid, alg)

    logger.info("JWKS initialised — %d key(s) loaded.", len(_jwks_cache))


def _get_public_key(kid: Optional[str]) -> object:
    """Return the cached public key for *kid*, or the first key if kid is None."""
    if not _jwks_cache:
        raise RuntimeError(
            "JWKS cache is empty. Ensure init_jwks() ran successfully at startup."
        )
    if kid and kid in _jwks_cache:
        return _jwks_cache[kid]
    # Fall back to first key if kid not found or not present in token
    return next(iter(_jwks_cache.values()))


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict:
    """FastAPI dependency — verifies a Supabase JWT bearer token locally.

    No network call is made per request. The token is verified against the
    EC public key cached at startup via init_jwks().

    Returns:
        The decoded JWT payload dict (sub, email, role, exp, …).

    Raises:
        HTTPException 401: Token is missing, malformed, expired, or has a bad signature.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Read kid + alg from the unverified header to select the right key
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        alg = header.get("alg", "ES256")
        logger.debug("JWT header — alg: %s  kid: %s", alg, kid)
    except jwt.DecodeError as exc:
        logger.warning("Malformed JWT header: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    public_key = _get_public_key(kid)

    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[alg],
            options={"verify_aud": False},
        )
        logger.debug("JWT verified OK — sub: %s", payload.get("sub"))
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT expired for sub: %s", jwt.decode(
            token, options={"verify_signature": False}
        ).get("sub", "unknown"))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as exc:
        logger.warning("JWT verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
