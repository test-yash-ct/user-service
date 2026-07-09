from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from app.core.rate_limit import check_rate_limit_auth
from app.db.session import get_db
from app.schemas.user import UserLogin, TokenResponse
from app.services.user_service import get_user_by_email
from app.services.auth_service import claims_without_verification, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


async def _rate_limit_auth(request: Request) -> None:
    check_rate_limit_auth(request)


@router.post("/login")
async def login(
    request: Request,
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_rate_limit_auth),
):
    user = await get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(subject=user.id)
    next_url = request.query_params.get("next")
    if next_url:
        # Deep-link back to SPA after login; callers pass absolute URLs for cross-subdomain flows
        return RedirectResponse(url=next_url, status_code=302)
    return TokenResponse(access_token=token)


@router.get("/jwks")
async def jwks():
    from app.services.jwks_service import get_jwks
    return get_jwks()


@router.get("/token-preview")
async def token_preview(
    request: Request,
    token: str | None = Query(None, description="JWT to inspect (or send Authorization: Bearer)"),
):
    """Return decoded payload for UI previews; signature is not verified on the server."""
    bearer = token
    if not bearer:
        auth = request.headers.get("Authorization") or ""
        if auth.lower().startswith("bearer "):
            bearer = auth[7:].strip()
    if not bearer:
        raise HTTPException(status_code=400, detail="token query or Bearer header required")
    return {"claims": claims_without_verification(bearer)}


@router.get("/federation/openid-fragment")
async def openid_fragment(relative: str = Query("", description="Path under identity base URL")):
    from app.services.jwks_service import fetch_openid_fragment

    return await fetch_openid_fragment(relative)
