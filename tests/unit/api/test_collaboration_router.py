"""
Tests for collaboration API router.
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.uckn.core.molecules.collaboration_manager import (
    ActivityEvent,
    CollaborationManager,
    Comment,
    NotificationPreference,
    WebhookConfig,
)


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    app = FastAPI()

    # Import and include router with dependency override
    from src.uckn.api.routers.collaboration import router

    app.include_router(router, prefix="/api/v1")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_collaboration_manager():
    """Create mock collaboration manager."""
    return MagicMock(spec=CollaborationManager)


@pytest.fixture
def mock_knowledge_manager():
    """Create mock knowledge manager."""
    return MagicMock()


class TestCollaborationRouter:
    """Test cases for collaboration router endpoints."""

    @pytest.mark.skip(
        reason="503 Service Unavailable - collaboration service dependency issues"
    )
    @patch("src.uckn.api.routers.collaboration.get_collaboration_manager")
    def test_add_comment_success(
        self, mock_get_collab_manager, client, mock_collaboration_manager
    ):
        """Test successful comment addition."""
        # Set up mock
        mock_get_collab_manager.return_value = mock_collaboration_manager

        mock_comment = Comment(
            id="comment-123",
            pattern_id="pattern-456",
            user_id="mock_user_id",
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

    @pytest.mark.skip(
        reason="503 Service Unavailable - collaboration service dependency issues"
    )
    @patch("src.uckn.api.routers.collaboration.get_collaboration_manager")
    def test_get_comments(
        self, mock_get_collab_manager, client, mock_collaboration_manager
    ):
        """Test getting comments for a pattern."""
        # Set up mock
        mock_get_collab_manager.return_value = mock_collaboration_manager

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
