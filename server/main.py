"""
Sentry AI — FastAPI Application Entry Point
Configures CORS, security headers, observability middleware.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from config import settings
from middleware import ObservabilityMiddleware
from models.response import BaseResponse
from routers import events, scenarios, cases, actions
import store.audit

# ── Logging ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-28s  %(levelname)-5s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sentry.main")


# ── Lifespan ──────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("Sentry AI starting  —  DEMO_MODE=%s", settings.DEMO_MODE)
    await store.audit.init_db()
    yield
    logger.info("Sentry AI shutting down")


# ── App Instance ──────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered security triage agent — hackathon MVP",
    lifespan=lifespan,
)

# ── CORS (wide-open for hackathon dev) ────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Observability Middleware ──────────────────────────────────────
app.add_middleware(ObservabilityMiddleware)


# ── Security Headers Middleware ───────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Bank-grade security headers applied to every response.
    Protects against XSS, clickjacking, MIME sniffing, and more.
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=()"
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
    )
    return response


# ── Routers ───────────────────────────────────────────────────────
app.include_router(events.router)
app.include_router(scenarios.router)
app.include_router(cases.router)
app.include_router(actions.router)


# ── Health Endpoint ───────────────────────────────────────────────
@app.get("/health", response_model=BaseResponse[dict], tags=["System"])
async def health_check() -> BaseResponse[dict]:
    """Health check — returns server status and version."""
    return BaseResponse(
        status="success",
        data={
            "status": "ok",
            "version": settings.APP_VERSION,
            "demo_mode": settings.DEMO_MODE,
        },
        message="Sentry AI is running",
    )


# ── Global Exception Handler ─────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all that still returns the BaseResponse envelope."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content=BaseResponse(
            status="error",
            data=None,
            message="Internal server error",
        ).model_dump(),
    )
