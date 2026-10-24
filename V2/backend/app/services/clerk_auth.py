import os
from functools import lru_cache

import jwt


class ClerkAuthError(Exception):
    pass


@lru_cache(maxsize=8)
def _jwks_client(jwks_url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(jwks_url)


def _derive_jwks_url(token: str) -> tuple[str, str | None]:
    try:
        claims = jwt.decode(token, options={"verify_signature": False})
    except Exception as exc:
        raise ClerkAuthError("Token could not be decoded.") from exc

    issuer = claims.get("iss")
    if not issuer:
        raise ClerkAuthError("Token is missing issuer claim.")

    trusted_issuer = os.getenv('CLERK_ISSUER', '').strip()
    configured_jwks = os.getenv('CLERK_JWKS_URL', '').strip()
    if not trusted_issuer and not configured_jwks:
        raise ClerkAuthError('Configure CLERK_ISSUER or CLERK_JWKS_URL before verifying accounts.')
    if trusted_issuer and issuer.rstrip('/') != trusted_issuer.rstrip('/'):
        raise ClerkAuthError('Token issuer does not match the configured account service.')

    jwks_url = configured_jwks or f"{trusted_issuer.rstrip('/')}/.well-known/jwks.json"
    return jwks_url, issuer


def verify_clerk_token(token: str) -> dict:
    jwks_url, token_issuer = _derive_jwks_url(token)

    try:
        signing_key = _jwks_client(jwks_url).get_signing_key_from_jwt(token)
    except Exception as exc:
        raise ClerkAuthError("Unable to fetch signing key for token.") from exc

    issuer = os.getenv("CLERK_ISSUER") or token_issuer
    audience = os.getenv("CLERK_AUDIENCE")

    decode_kwargs = {
        "key": signing_key.key,
        "algorithms": ["RS256"],
        "issuer": issuer,
        "options": {"verify_aud": bool(audience)},
    }
    if audience:
        decode_kwargs["audience"] = audience

    try:
        payload = jwt.decode(token, **decode_kwargs)
    except jwt.InvalidTokenError as exc:
        raise ClerkAuthError("Token signature or claims are invalid.") from exc

    return payload
