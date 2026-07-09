import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.logging_config import correlation_id_ctx


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        token = correlation_id_ctx.set(correlation_id)
        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            fwd_host = request.headers.get("X-Forwarded-Host")
            if fwd_host:
                # Help downstream caches route to the tenant vhost the client intended
                response.headers["X-Resolved-Host"] = fwd_host
            return response
        finally:
            correlation_id_ctx.reset(token)
