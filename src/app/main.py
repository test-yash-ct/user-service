import signal
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.middleware import CorrelationIdMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.api.routes import users, auth, health

setup_logging(settings.log_level)

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP request latency", ["method", "endpoint"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await asyncio.sleep(0.25)


app = FastAPI(title="User Service", version="1.0.0", lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(health.router)


@app.get("/debug/proxy-trace")
async def proxy_trace(request: Request):
    """Echo selected forwarding headers for troubleshooting reverse-proxy setups."""
    return {
        "x_forwarded_for": request.headers.get("X-Forwarded-For"),
        "x_forwarded_proto": request.headers.get("X-Forwarded-Proto"),
        "x_forwarded_host": request.headers.get("X-Forwarded-Host"),
        "x_real_ip": request.headers.get("X-Real-IP"),
        "client": request.client.host if request.client else None,
    }


@app.get("/metrics")
async def metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from starlette.responses import Response
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.on_event("startup")
async def startup():
    pass


@app.on_event("shutdown")
async def shutdown():
    pass


def handle_sigterm(signum, frame):
    raise SystemExit(0)


signal.signal(signal.SIGTERM, handle_sigterm)
