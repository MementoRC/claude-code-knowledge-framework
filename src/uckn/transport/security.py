"""
Security utilities for UCKN HTTP server.

Features:
- Localhost-only binding
- Origin validation
- Optional API key authentication
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


@dataclass
class SecurityConfig:
    """Security configuration for HTTP server."""

    localhost_only: bool = True
    allowed_origins: list[str] = field(default_factory=list)
    require_api_key: bool = False
    api_key: str | None = None

    def __post_init__(self) -> None:
        if not self.allowed_origins:
            self.allowed_origins = [
                "http://localhost",
                "http://127.0.0.1",
                "https://localhost",
                "https://127.0.0.1",
                "null",  # For file:// origins
            ]


class LocalhostOnlyMiddleware(BaseHTTPMiddleware):
    """Middleware that only allows localhost connections.

    This is a critical security feature - the HTTP server should NEVER
    be exposed to the network as it provides access to knowledge data.
    """

    ALLOWED_HOSTS = {"127.0.0.1", "::1", "localhost"}

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        client_host = request.client.host if request.client else None

        if client_host not in self.ALLOWED_HOSTS:
            logger.warning(f"Rejected connection from non-localhost: {client_host}")
            return Response(
                content="Only localhost connections are allowed",
                status_code=403,
                media_type="text/plain",
            )

        return await call_next(request)


def validate_origin(request: Request, allowed_origins: list[str]) -> bool:
    """Validate Origin header against allowed list."""
    origin = request.headers.get("Origin")

    if not origin:
        return True  # No origin header (same-origin request)

    for allowed in allowed_origins:
        if origin.startswith(allowed):
            return True

    logger.warning(f"Rejected request from disallowed origin: {origin}")
    return False


def validate_api_key(provided_key: str | None, expected_key: str) -> None:
    """Validate API key."""
    if not provided_key or provided_key != expected_key:
        logger.warning("Invalid or missing API key")
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def get_origin_validation_middleware(allowed_origins: list[str]) -> type:
    """Create origin validation middleware with configured allowed origins."""

    class OriginValidationMiddleware(BaseHTTPMiddleware):
        async def dispatch(
            self,
            request: Request,
            call_next: Callable[[Request], Awaitable[Response]],
        ) -> Response:
            if not validate_origin(request, allowed_origins):
                return Response(
                    content="Origin not allowed",
                    status_code=403,
                    media_type="text/plain",
                )
            return await call_next(request)

    return OriginValidationMiddleware
