"""Authentication Middleware for UCKN API"""

import logging

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from ..dependencies import get_settings, get_user_context, validate_api_key

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for API key validation"""

    # Endpoints that don't require authentication
    PUBLIC_ENDPOINTS = {
        "/docs",
        "/redoc",
        "/openapi.json",
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
        if not validate_api_key(api_key):
            logger.warning(f"Invalid API key for request to {request.url.path}")
            return self._unauthorized_response("Invalid API key")

        # Get user context and add to request state
        try:
            user_context = get_user_context(api_key)
            request.state.user = user_context
            request.state.api_key = api_key

            logger.debug(
                f"Authenticated user {user_context.get('user_id')} for {request.url.path}"
            )
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
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

    def _unauthorized_response(self, message: str) -> Response:
        """Return unauthorized response"""
        return Response(
            content=f'{{"error": "{message}", "status_code": 401}}',
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"Content-Type": "application/json"},
        )


def get_current_user(request: Request) -> dict:
    """Get current authenticated user from request state"""
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    return request.state.user


def require_permission(permission: str):
    """Decorator to require specific permission"""

    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            user = get_current_user(request)
            user_permissions = user.get("permissions", [])

            if permission not in user_permissions and "admin" not in user.get(
                "roles", []
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required",
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_role(role: str):
    """Decorator to require specific role"""

    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            user = get_current_user(request)
            user_roles = user.get("roles", [])

            if role not in user_roles and "admin" not in user_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{role}' required",
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator
