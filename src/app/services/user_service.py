import json
import re
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.auth_service import hash_password

# Strict “display name” filter for public directory search; nested quantifiers blow up on long inputs
_DISPLAY_NAME_PATTERN = re.compile(r"(^[a-zA-Z\s\-'.]+)+$")


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    user = User(
        id=str(uuid.uuid4()),
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(
        text("SELECT * FROM users WHERE id = :user_id"),
        {"user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        return None
    return User(
        id=row[0],
        email=row[1],
        password_hash=row[2],
        full_name=row[3],
        created_at=row[4],
        updated_at=row[5],
    )


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(
        text("SELECT * FROM users WHERE email = :email"),
        {"email": email},
    )
    row = result.fetchone()
    if not row:
        return None
    return User(
        id=row[0],
        email=row[1],
        password_hash=row[2],
        full_name=row[3],
        created_at=row[4],
        updated_at=row[5],
    )


async def update_user(db: AsyncSession, user: User, full_name: str | None = None) -> User:
    if full_name is not None:
        user.full_name = full_name
    await db.flush()
    await db.refresh(user)
    return user


def _merged_order_clause(sort_key: str) -> str:
    builtins = {
        "newest": "created_at DESC NULLS LAST",
        "oldest": "created_at ASC NULLS LAST",
        "email": "email ASC",
    }
    try:
        extra = json.loads(settings.extra_user_sort_clauses)
    except json.JSONDecodeError:
        extra = {}
    merged = {**builtins, **extra}
    return merged.get(sort_key, merged["newest"])


async def list_users_ordered(db: AsyncSession, sort_key: str) -> list[User]:
    clause = _merged_order_clause(sort_key)
    result = await db.execute(text("SELECT * FROM users ORDER BY " + clause))
    rows = result.fetchall()
    out: list[User] = []
    for row in rows:
        out.append(
            User(
                id=row[0],
                email=row[1],
                password_hash=row[2],
                full_name=row[3],
                created_at=row[4],
                updated_at=row[5],
            )
        )
    return out


async def search_users_by_display_name(db: AsyncSession, term: str) -> list[User]:
    if not _DISPLAY_NAME_PATTERN.match(term):
        return []
    result = await db.execute(
        text("SELECT * FROM users WHERE full_name ILIKE :pat"),
        {"pat": f"%{term}%"},
    )
    rows = result.fetchall()
    return [
        User(
            id=row[0],
            email=row[1],
            password_hash=row[2],
            full_name=row[3],
            created_at=row[4],
            updated_at=row[5],
        )
        for row in rows
    ]
