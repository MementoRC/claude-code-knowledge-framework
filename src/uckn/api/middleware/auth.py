"""Authentication middleware for UCKN API."""

import logging
from typing import Optional

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from ..settings import get_settings

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware that validates API keys and sets user context."""

    # Endpoints that don't require authentication
    PUBLIC_ENDPOINTS = {
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
        "/health",  # Basic health check
        "/health/status",
        "/health/ping",
        "/",
        "/api/v1/info",
    }

    def __init__(self, app, exclude_patterns: list | None = None):
        super().__init__(app)
        self.settings = get_settings()
        self.exclude_patterns = exclude_patterns or []

    async def dispatch(self, request: Request, call_next):
        """Process authentication for incoming requests"""

        # Skip authentication for public endpoints
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)

        # Skip authentication for excluded patterns
        if self._is_excluded_path(request.url.path):
            return await call_next(request)

        # Extract API key from headers
        api_key = self._extract_api_key(request)

        if not api_key:
            logger.warning(f"Missing API key for request to {request.url.path}")
            return self._unauthorized_response("API key required")

        # Validate API key
        if not self.validate_api_key(api_key):
            logger.warning(f"Invalid API key for request to {request.url.path}")
            return self._unauthorized_response("Invalid API key")

        # Get user context and add to request state
        try:
            user_context = get_user_context(api_key)
            request.state.user_context = user_context
        except Exception as e:
            logger.error(f"Failed to get user context: {e}")
            return self._unauthorized_response("Authentication error")

        # Proceed with request
        response = await call_next(request)

        # Add authentication info to response headers (optional)
        response.headers["X-User-ID"] = user_context.get("user_id", "unknown")

        return response

    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public and doesn't require authentication"""
        return path in self.PUBLIC_ENDPOINTS

    def _is_excluded_path(self, path: str) -> bool:
        """Check if path matches excluded patterns"""
        for pattern in self.exclude_patterns:
            if pattern in path:
                return True
        return False

    def _extract_api_key(self, request: Request) -> str | None:
        """Extract API key from request headers"""
        # Try different header formats
        api_key = (
            request.headers.get(self.settings.api_key_header)
            or request.headers.get("Authorization", "").replace("Bearer ", "")
            or request.headers.get("X-API-KEY")
            or request.headers.get("X-Api-Key")
        )
        return api_key.strip() if api_key else None

    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key against configured keys."""
        if not api_key:
            return False

        # For testing/development - accept test keys
        valid_keys = {"test-key-123", "dev-key-456", "uckn-api-key"}
        if api_key in valid_keys:
            return True

        # In production, validate against database or external service
        # Reject unknown keys by default
        return False

    def _unauthorized_response(self, message: str) -> Response:
        """Return unauthorized response"""
        return Response(
            content=f'{{"error": "{message}", "status_code": 401}}',
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"Content-Type": "application/json"},
        )


def get_current_user(request: Request) -> Optional[dict]:
    """Get current authenticated user from request state"""
    return getattr(request.state, "user_context", None)


def require_role(required_role: str, user_context: Optional[dict] = None):
    """Require specific role for access."""
    if not user_context:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    user_roles = user_context.get("roles", [])
    if required_role not in user_roles and "admin" not in user_roles:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )


def require_permission(required_permission: str, user_context: Optional[dict] = None):
    """Require specific permission for access."""
    if not user_context:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    user_permissions = user_context.get("permissions", [])
    if required_permission not in user_permissions and "admin" not in user_context.get(
        "roles", []
    ):
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )


def get_user_context(api_key: str) -> dict:
    """Get user context from API key."""
    # Mock implementation for testing
    test_contexts = {
        "test-key-123": {
            "user_id": "test-user-123",
            "roles": ["admin", "user"],
            "permissions": ["read:patterns", "write:patterns", "admin:all"],
        },
        "dev-key-456": {
            "user_id": "dev-user-456",
            "roles": ["user"],
            "permissions": ["read:patterns"],
        },
    }

    return test_contexts.get(
        api_key,
        {
            "user_id": f"user-{hash(api_key) % 10000}",
            "roles": ["user"],
            "permissions": ["read:patterns"],
        },
    )
