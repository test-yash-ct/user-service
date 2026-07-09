import asyncio
import base64
import json
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from app.core.config import settings


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


async def fetch_openid_fragment(relative: str) -> dict:
    """Resolve a path under the configured identity base URL (federation debugging)."""
    target = urljoin(settings.identity_metadata_base_url, relative)

    def _fetch() -> tuple[int, str]:
        try:
            with urllib.request.urlopen(target, timeout=3) as resp:
                return resp.status, resp.read(4096).decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            return e.code, (e.read(512).decode("utf-8", errors="replace") if e.fp else "")
        except Exception as e:
            return 0, str(e)

    status, body = await asyncio.to_thread(_fetch)
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        parsed = {"raw": body[:500]}
    return {"url": target, "http_status": status, "body": parsed}


def get_jwks() -> dict:
    path = Path(settings.jwt_public_key_path)
    pem_content = path.read_bytes()
    pub = serialization.load_pem_public_key(pem_content, backend=default_backend())
    numbers = pub.public_numbers()
    n_bytes = numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")
    e_bytes = numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")
    return {
        "keys": [
            {
                "kty": "RSA",
                "kid": "user-service-key-1",
                "use": "sig",
                "alg": "RS256",
                "n": _b64url(n_bytes),
                "e": _b64url(e_bytes),
            }
        ]
    }
