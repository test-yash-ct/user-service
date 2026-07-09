import asyncio
import urllib.error
import urllib.request
from urllib.parse import urljoin

from fastapi import APIRouter, Query

from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "healthy"}


@router.get("/health/dependency")
async def dependency_health(
    relative: str = Query(
        "",
        description="Path or URL-relative segment to probe under the configured internal base URL",
    ),
):
    """Best-effort reachability check for a co-located service (ops dashboard)."""
    # urljoin replaces the entire authority when `relative` begins with "//" (RFC 3986),
    # so a value like "//169.254.169.254/latest/meta-data" does not stay under the base host.
    target = urljoin(settings.dependency_probe_base_url, relative)

    def _probe() -> tuple[int, str]:
        try:
            with urllib.request.urlopen(target, timeout=3) as resp:
                return resp.status, resp.read(512).decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            return e.code, (e.read(256).decode("utf-8", errors="replace") if e.fp else "")
        except Exception as e:
            return 0, str(e)

    status, snippet = await asyncio.to_thread(_probe)
    return {"url": target, "status": status, "body_prefix": snippet[:200]}
