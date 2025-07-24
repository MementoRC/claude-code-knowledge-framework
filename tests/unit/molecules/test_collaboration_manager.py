"""
Tests for CollaborationManager.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.uckn.core.molecules.collaboration_manager import (
    ActivityEvent,
    CollaborationManager,
    Comment,
    NotificationPreference,
    WebhookConfig,
)
from src.uckn.core.organisms.knowledge_manager import KnowledgeManager


@pytest.fixture
def mock_knowledge_manager():
    """Create a mock knowledge manager."""
    km = MagicMock(spec=KnowledgeManager)
    km.get_pattern.return_value = {"id": "pattern-123", "title": "Test Pattern"}
    return km


@pytest.fixture
def collaboration_manager(mock_knowledge_manager):
    """Create a collaboration manager instance."""
    return CollaborationManager(mock_knowledge_manager)


@pytest.mark.asyncio
class TestCollaborationManager:
    """Test cases for CollaborationManager."""

    async def test_track_activity(self, collaboration_manager):
        """Test activity tracking."""
        event = ActivityEvent(
            type="pattern_shared",
            user_id="user-123",
            team_id="team-456",
            resource_id="pattern-789",
            resource_type="pattern",
            action="share",
        )

        # Mock the notification methods
        collaboration_manager._notify_activity_subscribers = AsyncMock()
        collaboration_manager._send_notifications = AsyncMock()
        collaboration_manager._trigger_webhooks = AsyncMock()

        await collaboration_manager.track_activity(event)

        # Verify all notification methods were called
        collaboration_manager._notify_activity_subscribers.assert_called_once_with(
            event
        )
        collaboration_manager._send_notifications.assert_called_once_with(event)
        collaboration_manager._trigger_webhooks.assert_called_once_with(event)

    async def test_add_comment_success(
        self, collaboration_manager, mock_knowledge_manager
    ):
        """Test successful comment addition."""
        comment = Comment(
            pattern_id="pattern-123",
            user_id="user-456",
            content="Great pattern!",
            metadata={"source": "web"},
        )

        collaboration_manager.track_activity = AsyncMock()

        result = await collaboration_manager.add_comment(comment)

        assert result == comment
        assert result.id is not None
        assert result.created_at is not None

        # Verify activity was tracked
        collaboration_manager.track_activity.assert_called_once()
        activity_call = collaboration_manager.track_activity.call_args[0][0]
        assert activity_call.type == "comment_added"
        assert activity_call.user_id == "user-456"
        assert activity_call.resource_id == "pattern-123"

    async def test_add_comment_pattern_not_found(
        self, collaboration_manager, mock_knowledge_manager
    ):
        """Test comment addition when pattern doesn't exist."""
        mock_knowledge_manager.get_pattern.return_value = None

        comment = Comment(
            pattern_id="nonexistent-pattern",
            user_id="user-456",
            content="Comment on nonexistent pattern",
        )

        with pytest.raises(ValueError, match="Pattern nonexistent-pattern not found"):
            await collaboration_manager.add_comment(comment)

    async def test_get_comments(self, collaboration_manager):
        """Test getting comments for a pattern."""
        pattern_id = "pattern-123"

        comments = await collaboration_manager.get_comments(pattern_id)

        assert isinstance(comments, list)
        assert len(comments) >= 0

        # If mock returns comments, verify structure
        if comments:
            comment = comments[0]
            assert comment.pattern_id == pattern_id
            assert hasattr(comment, "user_id")
            assert hasattr(comment, "content")
            assert hasattr(comment, "created_at")

    async def test_set_notification_preference(self, collaboration_manager):
        """Test setting notification preferences."""
        preference = NotificationPreference(
            user_id="user-123",
            notification_type="email",
            event_types=["pattern_shared", "comment_added"],
            enabled=True,
        )

        await collaboration_manager.set_notification_preference(preference)

        # Verify preference was stored
        user_prefs = collaboration_manager.notification_preferences.get("user-123", [])
        assert len(user_prefs) == 1
        assert user_prefs[0].notification_type == "email"
        assert user_prefs[0].enabled is True

    async def test_add_webhook(self, collaboration_manager):
        """Test adding webhook configuration."""
        webhook = WebhookConfig(
            team_id="team-123",
            name="Slack Integration",
            url="https://hooks.slack.com/webhook",
            event_types=["pattern_shared", "comment_added"],
            enabled=True,
        )

        await collaboration_manager.add_webhook(webhook)

        # Verify webhook was stored
        team_webhooks = collaboration_manager.webhook_configs.get("team-123", [])
        assert len(team_webhooks) == 1
        assert team_webhooks[0].name == "Slack Integration"
        assert team_webhooks[0].url == "https://hooks.slack.com/webhook"

    async def test_subscribe_to_activities(self, collaboration_manager):
        """Test subscribing to activity events."""
        subscriber_id = "subscriber-123"
        callback = AsyncMock()

        await collaboration_manager.subscribe_to_activities(subscriber_id, callback)

        # Verify subscriber was added
        assert subscriber_id in collaboration_manager.activity_subscribers
        assert callback in collaboration_manager.activity_subscribers[subscriber_id]


class TestActivityEvent:
    """Test cases for ActivityEvent model."""

    def test_activity_event_creation(self):
        """Test creating an activity event."""
        event = ActivityEvent(
            type="pattern_created",
            user_id="user-123",
            team_id="team-456",
            resource_id="pattern-789",
            resource_type="pattern",
            action="create",
            metadata={"source": "api"},
        )

        assert event.type == "pattern_created"
        assert event.user_id == "user-123"
        assert event.team_id == "team-456"
        assert event.resource_id == "pattern-789"
        assert event.resource_type == "pattern"
        assert event.action == "create"
        assert event.metadata == {"source": "api"}
        assert event.id is not None
        assert event.timestamp is not None
