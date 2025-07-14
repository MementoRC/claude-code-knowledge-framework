"""
Tests for collaboration API router.
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import the actual dependencies to override them
from src.uckn.api.dependencies import (
    get_knowledge_manager as original_get_knowledge_manager,
)
from src.uckn.api.routers.collaboration import (
    get_collaboration_manager as original_get_collaboration_manager,
)
from src.uckn.api.routers.collaboration import router  # Import the router itself
from src.uckn.core.molecules.collaboration_manager import (
    ActivityEvent,
    CollaborationManager,
    Comment,
    NotificationPreference,
    WebhookConfig,
)


@pytest.fixture
def app(mock_knowledge_manager, mock_collaboration_manager):
    """Create FastAPI app for testing with dependency overrides."""
    app = FastAPI()

    # Override dependencies
    app.dependency_overrides[original_get_knowledge_manager] = (
        lambda: mock_knowledge_manager
    )
    app.dependency_overrides[original_get_collaboration_manager] = (
        lambda: mock_collaboration_manager
    )

    app.include_router(router, prefix="/api/v1")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_collaboration_manager():
    """Create mock collaboration manager."""
    mock_manager = MagicMock(spec=CollaborationManager)
    # Explicitly make async methods AsyncMock
    mock_manager.add_comment = AsyncMock()
    mock_manager.get_comments = AsyncMock()
    mock_manager.get_activity_feed = AsyncMock()
    mock_manager.set_notification_preference = AsyncMock()
    mock_manager.add_webhook = AsyncMock()
    return mock_manager


@pytest.fixture
def mock_knowledge_manager():
    """Create mock knowledge manager."""
    # The knowledge manager is used by CollaborationManager constructor
    # and also by the share_pattern endpoint directly.
    # It needs to have a get_pattern method if share_pattern is tested.
    mock_km = MagicMock()
    # Provide a default return value for get_pattern if it's called by other endpoints
    mock_km.get_pattern.return_value = {"id": "pattern-456", "name": "Test Pattern"}
    return mock_km


class TestCollaborationRouter:
    """Test cases for collaboration router endpoints."""

    # No need for @patch here as dependencies are overridden in the app fixture
    def test_add_comment_success(self, client, mock_collaboration_manager):
        """Test successful comment addition."""
        # Set up mock return value for the async method
        mock_comment = Comment(
            id="comment-123",
            pattern_id="pattern-456",
            user_id="mock_user_id",  # This is hardcoded in the endpoint
            content="Great pattern!",
            metadata={"source": "web"},
            created_at=datetime.now(timezone.utc),
        )
        mock_collaboration_manager.add_comment.return_value = mock_comment

        # Make request
        response = client.post(
            "/api/v1/patterns/pattern-456/comments",
            json={"content": "Great pattern!", "metadata": {"source": "web"}},
        )

        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content}")
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "comment-123"
        assert data["pattern_id"] == "pattern-456"
        assert data["content"] == "Great pattern!"
        assert data["user_id"] == "mock_user_id"
        # Verify the mock was called correctly
        mock_collaboration_manager.add_comment.assert_called_once()
        # Optionally, check the arguments passed to add_comment
        called_comment = mock_collaboration_manager.add_comment.call_args[0][0]
        assert called_comment.pattern_id == "pattern-456"
        assert called_comment.user_id == "mock_user_id"
        assert called_comment.content == "Great pattern!"

    def test_get_comments(self, client, mock_collaboration_manager):
        """Test getting comments for a pattern."""
        # Set up mock return value for the async method
        mock_comments = [
            Comment(
                id="comment-1",
                pattern_id="pattern-123",
                user_id="user-1",
                content="First comment",
                created_at=datetime.now(timezone.utc),
            )
        ]
        mock_collaboration_manager.get_comments.return_value = mock_comments

        # Make request
        response = client.get("/api/v1/patterns/pattern-123/comments")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "comment-1"
        mock_collaboration_manager.get_comments.assert_called_once_with(
            "pattern-123", None
        )

    def test_create_pattern_library(self, client):
        """Test creating a team-scoped pattern library."""
        response = client.post(
            "/api/v1/teams/team-123/libraries",
            json={
                "name": "CI/CD Patterns",
                "description": "Common automation patterns",
                "pattern_ids": ["pattern-1", "pattern-2"],
                "settings": {"auto_sync": True},
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["team_id"] == "team-123"
        assert data["name"] == "CI/CD Patterns"
        assert "id" in data  # Ensure an ID is generated
        assert "created_at" in data  # Ensure timestamp is present
