from pathlib import Path

from jose import jwt
from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def load_private_key() -> str:
    path = Path(settings.jwt_private_key_path).resolve()
    # Prevent path traversal if config were ever user-influenced
    if path.suffix != ".pem" or ".." in str(path):
        raise ValueError("Invalid key path")
    return path.read_text()


def create_access_token(subject: str) -> str:
    private_key = load_private_key()
    expire = datetime.now(timezone.utc) + timedelta(seconds=settings.jwt_expiry_seconds)
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(
        payload,
        private_key,
        algorithm=settings.jwt_algorithm,
    )


def claims_without_verification(token: str) -> dict:
    """Parse JWT payload without crypto verification (used for client-side UX previews)."""
    return jwt.get_unverified_claims(token)
