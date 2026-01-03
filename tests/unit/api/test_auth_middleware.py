"""Minimal GREEN phase tests for AuthMiddleware."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, Request, Response
from starlette.datastructures import Headers

from uckn.api.middleware.auth import (
    AuthMiddleware,
    get_current_user,
    require_permission,
    require_role,
)


class TestAuthMiddleware:
    """Test AuthMiddleware functionality."""

    @pytest.fixture
    def auth_middleware(self):
        """Create AuthMiddleware instance."""
        return AuthMiddleware(app=None)

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/test"
        request.headers = Headers({})
        request.state = Mock()
        return request

    @pytest.mark.asyncio
    async def test_dispatch_no_auth_required(self, auth_middleware, mock_request):
        """Test middleware bypass for non-protected routes."""
        # Setup
        mock_request.url.path = "/health"
        call_next = AsyncMock(return_value=Response("OK"))

        # Execute
        response = await auth_middleware.dispatch(mock_request, call_next)

        # Assert
        assert response.body == b"OK"
        call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_dispatch_missing_api_key(self, auth_middleware, mock_request):
        """Test middleware rejects requests without API key."""
        # Setup
        mock_request.url.path = "/api/v1/patterns"
        call_next = AsyncMock()

        # Execute
        response = await auth_middleware.dispatch(mock_request, call_next)

        # Assert
        assert response.status_code == 401
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_invalid_api_key(self, auth_middleware, mock_request):
        """Test middleware rejects requests with invalid API key."""
        # Setup
        mock_request.url.path = "/api/v1/patterns"
        mock_request.headers = Headers({"X-API-Key": "invalid-key"})
        call_next = AsyncMock()

        # Execute
        response = await auth_middleware.dispatch(mock_request, call_next)

        # Assert
        assert response.status_code == 401
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_valid_api_key(self, auth_middleware, mock_request):
        """Test middleware allows requests with valid API key."""
        # Setup
        mock_request.url.path = "/api/v1/patterns"
        mock_request.headers = Headers({"X-API-Key": "test-key-123"})

        auth_middleware.settings.api_key_header = "X-API-Key"

        call_next = AsyncMock(return_value=Response("OK"))

        # Execute
        response = await auth_middleware.dispatch(mock_request, call_next)

        # Assert
        assert response.body == b"OK"
        call_next.assert_called_once_with(mock_request)

    def test_validate_api_key_valid(self, auth_middleware):
        """Test API key validation with valid key."""
        result = auth_middleware.validate_api_key("test-key-123")
        assert result is True

    def test_validate_api_key_invalid(self, auth_middleware):
        """Test API key validation with invalid key."""
        result = auth_middleware.validate_api_key("invalid-key")
        assert result is False

    def test_validate_api_key_empty(self, auth_middleware):
        """Test API key validation with empty key."""
        result = auth_middleware.validate_api_key("")
        assert result is False

    def test_validate_api_key_none(self, auth_middleware):
        """Test API key validation with None key."""
        result = auth_middleware.validate_api_key(None)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_context_success(self, auth_middleware, mock_request):
        """Test user context retrieval success."""
        # Setup
        mock_request.url.path = "/api/v1/patterns"
        mock_request.headers = Headers({"X-API-Key": "test-key-123"})

        auth_middleware.settings.api_key_header = "X-API-Key"

        # Mock get_user_context to return context
        with patch("uckn.api.middleware.auth.get_user_context") as mock_get_context:
            mock_get_context.return_value = {"user_id": "test-user", "roles": ["admin"]}

            call_next = AsyncMock(return_value=Response("OK"))

            # Execute
            response = await auth_middleware.dispatch(mock_request, call_next)

            # Assert
            assert response.body == b"OK"
            call_next.assert_called_once_with(mock_request)
            assert hasattr(mock_request.state, "user_context")

    @pytest.mark.asyncio
    async def test_get_user_context_error_handling(self, auth_middleware, mock_request):
        """Test user context error handling."""
        # Setup
        mock_request.url.path = "/api/v1/patterns"
        mock_request.headers = Headers({"X-API-Key": "test-key-123"})

        auth_middleware.settings.api_key_header = "X-API-Key"

        # Mock get_user_context to raise exception
        with patch("uckn.api.middleware.auth.get_user_context") as mock_get_context:
            mock_get_context.side_effect = Exception("Context error")

            call_next = AsyncMock()

            # Execute
            response = await auth_middleware.dispatch(mock_request, call_next)

            # Assert
            assert response.status_code == 401
            call_next.assert_not_called()


def test_get_current_user_with_state():
    """Test get_current_user with request state."""
    request = Mock()
    request.state.user_context = {"user_id": "test-user", "roles": ["admin"]}

    result = get_current_user(request)
    assert result == {"user_id": "test-user", "roles": ["admin"]}


def test_get_current_user_no_state():
    """Test get_current_user without request state."""
    request = Mock()
    request.state = Mock()
    del request.state.user_context  # Simulate missing user_context

    result = get_current_user(request)
    assert result is None


def test_require_role_valid():
    """Test require_role with valid role."""
    user_context = {"user_id": "test-user", "roles": ["admin"]}

    # Should not raise exception
    require_role("admin", user_context)


def test_require_role_invalid():
    """Test require_role with invalid role."""
    user_context = {"user_id": "test-user", "roles": ["user"]}

    with pytest.raises(HTTPException) as exc_info:
        require_role("admin", user_context)

    assert exc_info.value.status_code == 403
    assert "Insufficient permissions" in str(exc_info.value.detail)


def test_require_role_no_context():
    """Test require_role without user context."""
    with pytest.raises(HTTPException) as exc_info:
        require_role("admin", None)

    assert exc_info.value.status_code == 401
    assert "Authentication required" in str(exc_info.value.detail)


def test_require_permission_valid():
    """Test require_permission with valid permission."""
    user_context = {"user_id": "test-user", "permissions": ["read:patterns"]}

    # Should not raise exception
    require_permission("read:patterns", user_context)


def test_require_permission_invalid():
    """Test require_permission with invalid permission."""
    user_context = {"user_id": "test-user", "permissions": ["read:basic"]}

    with pytest.raises(HTTPException) as exc_info:
        require_permission("write:patterns", user_context)

    assert exc_info.value.status_code == 403
    assert "Insufficient permissions" in str(exc_info.value.detail)


def test_require_permission_no_context():
    """Test require_permission without user context."""
    with pytest.raises(HTTPException) as exc_info:
        require_permission("read:patterns", None)

    assert exc_info.value.status_code == 401
    assert "Authentication required" in str(exc_info.value.detail)
