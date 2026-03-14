"""
Sentry AI — Observability Middleware
Logs method, path, status code, and latency for every HTTP request.
Provides a clear audit trail for debugging and demo presentation.
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("sentry.observability")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware that wraps every request with structured timing logs.

    Log format:
        [REQUEST]  GET  /api/events  → 200  (12.3 ms)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        method = request.method
        path = request.url.path

        try:
            response: Response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "[REQUEST]  %s  %s  → 500  (%.1f ms)  UNHANDLED EXCEPTION",
                method, path, elapsed_ms,
            )
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "[REQUEST]  %s  %s  → %d  (%.1f ms)",
            method, path, response.status_code, elapsed_ms,
        )

        return response
