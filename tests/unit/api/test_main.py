"""Tests for API main module - FastAPI app initialization and lifespan."""

from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from uckn.api.main import app, global_exception_handler, lifespan


class TestLifespan:
    """Test application lifespan management."""

    @pytest.mark.asyncio
    async def test_lifespan_successful_startup(self):
        """Test successful application startup."""
        # Create mock FastAPI app
        mock_app = Mock(spec=FastAPI)

        # Mock KnowledgeManager and dependencies
        with (
            patch("uckn.api.main.KnowledgeManager") as mock_km_class,
            patch("uckn.api.main.set_knowledge_manager") as mock_set_km,
        ):
            # Setup mocks
            mock_km_instance = Mock()
            mock_km_class.return_value = mock_km_instance

            # Test lifespan context manager
            lifespan_cm = lifespan(mock_app)

            # Enter context (startup)
            await lifespan_cm.__aenter__()

            # Verify KnowledgeManager was created and set
            mock_km_class.assert_called_once()
            mock_set_km.assert_called_once_with(mock_km_instance)

            # Exit context (shutdown)
            await lifespan_cm.__aexit__(None, None, None)

    @pytest.mark.asyncio
    async def test_lifespan_startup_failure(self):
        """Test application startup failure handling."""
        mock_app = Mock(spec=FastAPI)

        # Mock KnowledgeManager to raise exception
        with patch("uckn.api.main.KnowledgeManager") as mock_km_class:
            mock_km_class.side_effect = Exception("Database connection failed")

            lifespan_cm = lifespan(mock_app)

            # Startup should raise the exception
            with pytest.raises(Exception) as exc_info:
                await lifespan_cm.__aenter__()

            assert str(exc_info.value) == "Database connection failed"


class TestGlobalExceptionHandler:
    """Test global exception handler."""

    @pytest.mark.asyncio
    async def test_global_exception_handler_returns_500(self):
        """Test that global exception handler returns 500 status."""
        # Create mock request and exception
        mock_request = Mock()
        test_exception = Exception("Something went wrong")

        # Call exception handler
        response = await global_exception_handler(mock_request, test_exception)

        # Verify response
        assert response.status_code == 500
        assert "Internal server error" in str(response.body)
        assert "internal_error" in str(response.body)


class TestAppConfiguration:
    """Test FastAPI app configuration."""

    def test_app_instance_created(self):
        """Test that FastAPI app instance is properly created."""
        assert isinstance(app, FastAPI)
        assert app.title == "Universal Claude Code Knowledge Network (UCKN) API"
        assert app.version == "1.0.0"
        assert app.docs_url == "/api/docs"
        assert app.redoc_url == "/api/redoc"
        assert app.openapi_url == "/api/openapi.json"

    def test_app_has_middleware(self):
        """Test that app has required middleware configured."""
        # Check if middleware is present (middleware is stored in user_middleware)
        middleware_classes = [middleware.cls for middleware in app.user_middleware]

        # Import middleware classes for comparison
        from fastapi.middleware.cors import CORSMiddleware

        from uckn.api.middleware.auth import AuthMiddleware
        from uckn.api.middleware.rate_limiting import RateLimitingMiddleware

        assert AuthMiddleware in middleware_classes
        assert RateLimitingMiddleware in middleware_classes
        assert CORSMiddleware in middleware_classes

    def test_app_has_routers(self):
        """Test that app has all required routers configured."""
        # Get all routes from the app
        routes = [route.path for route in app.routes]

        # Check for key endpoint patterns
        health_routes = [r for r in routes if r.startswith("/health")]
        api_routes = [r for r in routes if r.startswith("/api/v1")]

        assert len(health_routes) > 0  # Should have health endpoints
        assert len(api_routes) > 0  # Should have API v1 endpoints

        # Check for specific expected patterns
        expected_patterns = [
            "/health",
            "/api/v1/auth",
            "/api/v1/teams",
            "/api/v1/predictions",
            "/api/v1/patterns",
            "/api/v1/workflow",
            "/api/v1/projects",
            "/api/v1/collaboration",
        ]

        # At least some of these patterns should exist in routes
        matching_patterns = []
        for pattern in expected_patterns:
            for route in routes:
                if route.startswith(pattern):
                    matching_patterns.append(pattern)
                    break

        # Should have most of the expected patterns
        assert len(matching_patterns) >= len(expected_patterns) // 2

    def test_app_exception_handlers(self):
        """Test that app has global exception handlers configured."""
        # Check that Exception handler is registered
        assert Exception in app.exception_handlers
        assert app.exception_handlers[Exception] == global_exception_handler


class TestAppIntegration:
    """Integration tests for the FastAPI app."""

    def test_app_startup_without_errors(self):
        """Test that app can be instantiated without immediate errors."""
        # This tests basic app configuration without full startup
        with patch("uckn.api.main.KnowledgeManager") as mock_km:
            mock_km.return_value = Mock()

            # Create test client (this will trigger basic FastAPI setup)
            client = TestClient(app)

            # App should be created successfully
            assert client.app is app

    @pytest.mark.asyncio
    async def test_lifespan_integration_with_mocks(self):
        """Test lifespan integration with proper mocking."""
        # Mock all dependencies
        with (
            patch("uckn.api.main.KnowledgeManager") as mock_km_class,
            patch("uckn.api.main.set_knowledge_manager") as mock_set_km,
        ):
            mock_km_instance = Mock()
            mock_km_class.return_value = mock_km_instance

            # Create a test app with the same lifespan
            test_app = FastAPI(lifespan=lifespan)

            # Test the lifespan context
            lifespan_cm = lifespan(test_app)

            # Should complete without errors
            await lifespan_cm.__aenter__()
            await lifespan_cm.__aexit__(None, None, None)

            # Verify initialization was called
            mock_km_class.assert_called_once()
            mock_set_km.assert_called_once_with(mock_km_instance)

    def test_cors_configuration(self):
        """Test CORS middleware configuration."""
        # Find CORS middleware in the middleware stack
        cors_middleware = None
        for middleware in app.user_middleware:
            if hasattr(middleware, "cls"):
                from fastapi.middleware.cors import CORSMiddleware

                if middleware.cls == CORSMiddleware:
                    cors_middleware = middleware
                    break

        assert cors_middleware is not None

        # CORS should be configured (exact options depend on configuration)
        # Just verify it exists and has basic properties
        assert hasattr(cors_middleware, "kwargs")

    def test_middleware_order(self):
        """Test that middleware is added in correct order."""
        # Get middleware classes in order
        middleware_classes = [middleware.cls for middleware in app.user_middleware]

        from fastapi.middleware.cors import CORSMiddleware

        from uckn.api.middleware.auth import AuthMiddleware
        from uckn.api.middleware.rate_limiting import RateLimitingMiddleware

        # Find positions of key middleware
        auth_pos = -1
        rate_limit_pos = -1
        cors_pos = -1

        for i, cls in enumerate(middleware_classes):
            if cls == AuthMiddleware:
                auth_pos = i
            elif cls == RateLimitingMiddleware:
                rate_limit_pos = i
            elif cls == CORSMiddleware:
                cors_pos = i

        # All middleware should be present
        assert auth_pos >= 0
        assert rate_limit_pos >= 0
        assert cors_pos >= 0

        # Order should be: RateLimit -> Auth -> CORS (middleware stack is reversed)
        # So in the list, CORS appears first, then Auth, then RateLimit
        assert cors_pos < auth_pos < rate_limit_pos
