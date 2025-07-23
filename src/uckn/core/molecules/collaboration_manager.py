"""
Collaboration Manager for UCKN.

Manages real-time collaboration features including:
- Team-scoped pattern libraries
- Activity tracking and feeds
- Comment and discussion system
- Notification preferences
- Webhook integrations
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import aiohttp
from pydantic import BaseModel, Field

from ..organisms.knowledge_manager import KnowledgeManager

logger = logging.getLogger(__name__)


class ActivityEvent(BaseModel):
    """Activity event model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str
    user_id: str
    team_id: str | None = None
    resource_id: str | None = None
    resource_type: str | None = None
    action: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Comment(BaseModel):
    """Comment model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    pattern_id: str
    user_id: str
    parent_id: str | None = None  # For threaded comments
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = None


class NotificationPreference(BaseModel):
    """Notification preference model."""
    user_id: str
    notification_type: str  # email, in_app, webhook
    event_types: list[str]  # pattern_shared, comment_added, etc.
    settings: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class WebhookConfig(BaseModel):
    """Webhook configuration model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    team_id: str
    name: str
    url: str
    secret: str | None = None
    event_types: list[str]
    enabled: bool = True
    settings: dict[str, Any] = Field(default_factory=dict)


class CollaborationManager:
    """Manages collaboration features and real-time updates."""

    def __init__(self, knowledge_manager: KnowledgeManager):
        self.knowledge_manager = knowledge_manager
        self.activity_subscribers: dict[str, list[Callable]] = {}
        self.webhook_configs: dict[str, list[WebhookConfig]] = {}
        self.notification_preferences: dict[str, list[NotificationPreference]] = {}

    async def track_activity(self, event: ActivityEvent) -> None:
        """Track an activity event and notify subscribers."""
        try:
            # Store activity in database (mock implementation)
            logger.info(f"Activity tracked: {event.type} by {event.user_id}")

            # Notify subscribers
            await self._notify_activity_subscribers(event)

            # Send notifications based on preferences
            await self._send_notifications(event)

            # Trigger webhooks
            await self._trigger_webhooks(event)

        except Exception as e:
            logger.error(f"Error tracking activity: {e}")

    async def add_comment(self, comment: Comment) -> Comment:
        """Add a comment to a pattern."""
        try:
            # Validate pattern exists
            pattern = self.knowledge_manager.get_pattern(comment.pattern_id)
            if not pattern:
                raise ValueError(f"Pattern {comment.pattern_id} not found")

            # Store comment (mock implementation)
            logger.info(f"Comment added to pattern {comment.pattern_id} by {comment.user_id}")

            # Track activity
            activity = ActivityEvent(
                type="comment_added",
                user_id=comment.user_id,
                resource_id=comment.pattern_id,
                resource_type="pattern",
                action="comment",
                metadata={
                    "comment_id": comment.id,
                    "parent_id": comment.parent_id,
                    "content_length": len(comment.content)
                }
            )
            await self.track_activity(activity)

            return comment

        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            raise

    async def get_comments(self, pattern_id: str, parent_id: str | None = None) -> list[Comment]:
        """Get comments for a pattern (optionally filtered by parent)."""
        try:
            # Mock implementation - in real version, query from database
            mock_comments = [
                Comment(
                    id="comment-1",
                    pattern_id=pattern_id,
                    user_id="user-1",
                    parent_id=parent_id,
                    content="This pattern looks useful for CI/CD automation.",
                    created_at=datetime.now(timezone.utc)
                )
            ]

            return mock_comments

        except Exception as e:
            logger.error(f"Error getting comments: {e}")
            return []

    async def get_activity_feed(self, team_id: str | None = None, limit: int = 50) -> list[ActivityEvent]:
        """Get activity feed for a team or user."""
        try:
            # Mock implementation - in real version, query from database
            mock_activities = [
                ActivityEvent(
                    type="pattern_shared",
                    user_id="user-1",
                    team_id=team_id,
                    resource_id="pattern-123",
                    resource_type="pattern",
                    action="share",
                    metadata={"shared_with": "team"},
                    timestamp=datetime.now(timezone.utc)
                ),
                ActivityEvent(
                    type="comment_added",
                    user_id="user-2",
                    team_id=team_id,
                    resource_id="pattern-123",
                    resource_type="pattern",
                    action="comment",
                    metadata={"comment_id": "comment-1"},
                    timestamp=datetime.now(timezone.utc)
                )
            ]

            return mock_activities[:limit]

        except Exception as e:
            logger.error(f"Error getting activity feed: {e}")
            return []

    async def set_notification_preference(self, preference: NotificationPreference) -> None:
        """Set notification preference for a user."""
        try:
            user_prefs = self.notification_preferences.get(preference.user_id, [])

            # Remove existing preference for the same notification type
            user_prefs = [p for p in user_prefs if p.notification_type != preference.notification_type]
            user_prefs.append(preference)

            self.notification_preferences[preference.user_id] = user_prefs

            logger.info(f"Notification preference set for user {preference.user_id}")

        except Exception as e:
            logger.error(f"Error setting notification preference: {e}")
            raise

    async def add_webhook(self, webhook: WebhookConfig) -> None:
        """Add webhook configuration for a team."""
        try:
            team_webhooks = self.webhook_configs.get(webhook.team_id, [])
            team_webhooks.append(webhook)
            self.webhook_configs[webhook.team_id] = team_webhooks

            logger.info(f"Webhook {webhook.name} added for team {webhook.team_id}")

        except Exception as e:
            logger.error(f"Error adding webhook: {e}")
            raise

    async def subscribe_to_activities(self, subscriber_id: str, callback: Callable[[ActivityEvent], None]) -> None:
        """Subscribe to activity events."""
        if subscriber_id not in self.activity_subscribers:
            self.activity_subscribers[subscriber_id] = []

        self.activity_subscribers[subscriber_id].append(callback)
        logger.info(f"Activity subscriber {subscriber_id} added")

    async def unsubscribe_from_activities(self, subscriber_id: str) -> None:
        """Unsubscribe from activity events."""
        if subscriber_id in self.activity_subscribers:
            del self.activity_subscribers[subscriber_id]
            logger.info(f"Activity subscriber {subscriber_id} removed")

    async def _notify_activity_subscribers(self, event: ActivityEvent) -> None:
        """Notify all activity subscribers of an event."""
        try:
            for subscriber_id, callbacks in self.activity_subscribers.items():
                for callback in callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(event)
                        else:
                            callback(event)
                    except Exception as e:
                        logger.error(f"Error notifying subscriber {subscriber_id}: {e}")
        except Exception as e:
            logger.error(f"Error notifying activity subscribers: {e}")

    async def _send_notifications(self, event: ActivityEvent) -> None:
        """Send notifications based on user preferences."""
        try:
            # Find users who should be notified for this event
            for user_id, preferences in self.notification_preferences.items():
                for pref in preferences:
                    if not pref.enabled or event.type not in pref.event_types:
                        continue

                    if pref.notification_type == "email":
                        await self._send_email_notification(user_id, event, pref)
                    elif pref.notification_type == "in_app":
                        await self._send_in_app_notification(user_id, event, pref)

        except Exception as e:
            logger.error(f"Error sending notifications: {e}")

    async def _send_email_notification(self, user_id: str, event: ActivityEvent, preference: NotificationPreference) -> None:
        """Send email notification (mock implementation)."""
        try:
            # Mock implementation - in real version, integrate with email service
            logger.info(f"Email notification sent to {user_id} for event {event.type}")

        except Exception as e:
            logger.error(f"Error sending email notification: {e}")

    async def _send_in_app_notification(self, user_id: str, event: ActivityEvent, preference: NotificationPreference) -> None:
        """Send in-app notification (mock implementation)."""
        try:
            # Mock implementation - in real version, store in user notification queue
            logger.info(f"In-app notification sent to {user_id} for event {event.type}")

        except Exception as e:
            logger.error(f"Error sending in-app notification: {e}")

    async def _trigger_webhooks(self, event: ActivityEvent) -> None:
        """Trigger webhooks for the event."""
        try:
            team_id = event.team_id
            if not team_id:
                return

            webhooks = self.webhook_configs.get(team_id, [])

            for webhook in webhooks:
                if not webhook.enabled or event.type not in webhook.event_types:
                    continue

                await self._send_webhook(webhook, event)

        except Exception as e:
            logger.error(f"Error triggering webhooks: {e}")

    async def _send_webhook(self, webhook: WebhookConfig, event: ActivityEvent) -> None:
        """Send webhook payload to external service."""
        try:
            payload = {
                "event_type": event.type,
                "event_id": event.id,
                "user_id": event.user_id,
                "team_id": event.team_id,
                "resource_id": event.resource_id,
                "resource_type": event.resource_type,
                "action": event.action,
                "metadata": event.metadata,
                "timestamp": event.timestamp.isoformat()
            }

            headers = {"Content-Type": "application/json"}
            if webhook.secret:
                # In real implementation, add HMAC signature
                headers["X-UCKN-Signature"] = f"sha256={webhook.secret}"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook {webhook.name} delivered successfully")
                    else:
                        logger.warning(f"Webhook {webhook.name} failed with status {response.status}")

        except Exception as e:
            logger.error(f"Error sending webhook {webhook.name}: {e}")
