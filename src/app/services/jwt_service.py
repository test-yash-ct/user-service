import httpx
import logging
from jose import jwt, jwk
from jose.backends import RSAKey

from app.core.config import settings


logger = logging.getLogger(__name__)

async def fetch_jwks() -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(settings.user_service_jwks_url)
        response.raise_for_status()
        return response.json()


def get_signing_key(jwks: dict, token: str) -> RSAKey | None:
    unverified = jwt.get_unverified_header(token)
    kid = unverified.get("kid")
    for key_data in jwks.get("keys", []):
        if key_data.get("kid") == kid:
            return jwk.construct(key_data)
    # No fallback to arbitrary key - kid mismatch must fail verification
    logger.warning(f"JWT kid mismatch: token kid={kid} not found in JWKS")
    return None


async def verify_token(token: str) -> str | None:
    jwks = await fetch_jwks()
    key = get_signing_key(jwks, token)
    if not key:
        return None
    try:
        options = {"verify_aud": bool(settings.jwt_audience), "verify_iss": bool(settings.jwt_issuer)}
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options=options,
            audience=settings.jwt_audience or None,
            issuer=settings.jwt_issuer or None,
        )
        return payload.get("sub")
    except Exception:
        return None
