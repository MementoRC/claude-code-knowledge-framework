"""
Collaboration endpoints for UCKN API.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from pydantic import BaseModel, Field

from ...core.molecules.collaboration_manager import (
    CollaborationManager,
    NotificationPreference,
    WebhookConfig,
)
from ...core.molecules.collaboration_manager import (
    Comment as CollabComment,
)
from ...core.organisms.knowledge_manager import KnowledgeManager
from ..dependencies import get_knowledge_manager
from ..models.collaboration import (
    ActivityEventResponse,
    CommentRequest,
    CommentResponse,
    NotificationPreferenceRequest,
    NotificationPreferenceResponse,
    PatternLibraryRequest,
    PatternLibraryResponse,
    WebhookConfigRequest,
    WebhookConfigResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class SharingScope(BaseModel):
    """Sharing scope model."""

    scope_type: str = Field(
        ..., description="Type of sharing scope (public, team, private)"
    )
    team_id: str | None = None
    users: list[str] | None = None


class PatternShareRequest(BaseModel):
    """Request model for pattern sharing."""

    scope: SharingScope
    message: str | None = None


class PatternShareResponse(BaseModel):
    """Response model for pattern sharing."""

    pattern_id: str
    shared_with: str
    share_id: str
    message: str


class UpdateFilter(BaseModel):
    """Update filter model for WebSocket subscriptions."""

    pattern_types: list[str] | None = None
    technologies: list[str] | None = None
    projects: list[str] | None = None


class ConnectionManager:
    """WebSocket connection manager."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.connection_filters: dict[WebSocket, UpdateFilter] = {}

    async def connect(
        self, websocket: WebSocket, filters: UpdateFilter | None = None
    ):
        """Accept WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        if filters:
            self.connection_filters[websocket] = filters

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_filters:
            del self.connection_filters[websocket]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific WebSocket connection."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message to WebSocket: {e}")

    async def broadcast(self, message: str, filters: UpdateFilter | None = None):
        """Broadcast message to all connections matching filters."""
        for connection in self.active_connections:
            # Check if connection matches filter criteria
            if filters and connection in self.connection_filters:
                conn_filter = self.connection_filters[connection]
                # Simple filter matching logic (can be enhanced)
                if not self._matches_filter(filters, conn_filter):
                    continue

            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                # Remove broken connections
                self.disconnect(connection)

    def _matches_filter(
        self, message_filter: UpdateFilter, conn_filter: UpdateFilter
    ) -> bool:
        """Check if message filter matches connection filter."""
        # Simple implementation - can be enhanced
        if conn_filter.technologies and message_filter.technologies:
            return bool(
                set(conn_filter.technologies) & set(message_filter.technologies)
            )
        return True


# Global connection manager
manager = ConnectionManager()

# Global collaboration manager instance
collaboration_manager = None


def get_collaboration_manager(
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager),
) -> CollaborationManager:
    """Get collaboration manager instance."""
    global collaboration_manager
    if collaboration_manager is None:
        collaboration_manager = CollaborationManager(knowledge_manager)
    return collaboration_manager


@router.post("/patterns/{pattern_id}/share", response_model=PatternShareResponse)
async def share_pattern(
    pattern_id: str,
    request: PatternShareRequest,
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager),
):
    """Share a pattern with specified scope."""
    try:
        # Verify pattern exists
        pattern = knowledge_manager.get_pattern(pattern_id)
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")

        # Generate share ID (in real implementation, this would be stored in database)
        import uuid

        share_id = str(uuid.uuid4())

        # Determine sharing scope description
        if request.scope.scope_type == "public":
            shared_with = "public"
        elif request.scope.scope_type == "team" and request.scope.team_id:
            shared_with = f"team:{request.scope.team_id}"
        elif request.scope.scope_type == "private" and request.scope.users:
            shared_with = f"users:{','.join(request.scope.users)}"
        else:
            raise HTTPException(status_code=400, detail="Invalid sharing scope")

        # In a real implementation, store sharing info in database
        # For now, just return success response

        # Broadcast update to WebSocket connections
        update_message = {
            "type": "pattern_shared",
            "pattern_id": pattern_id,
            "shared_with": shared_with,
            "timestamp": "2024-01-01T00:00:00Z",  # Should use actual timestamp
        }

        import json

        await manager.broadcast(json.dumps(update_message))

        return PatternShareResponse(
            pattern_id=pattern_id,
            shared_with=shared_with,
            share_id=share_id,
            message=f"Pattern shared successfully with {shared_with}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sharing pattern: {e}")
        raise HTTPException(status_code=500, detail=f"Pattern sharing failed: {str(e)}")


@router.websocket("/updates/subscribe")
async def subscribe_to_updates(
    websocket: WebSocket,
    technologies: str | None = None,
    pattern_types: str | None = None,
    projects: str | None = None,
):
    """WebSocket endpoint for real-time updates subscription."""
    # Parse query parameters into filters
    filters = UpdateFilter()
    if technologies:
        filters.technologies = [t.strip() for t in technologies.split(",")]
    if pattern_types:
        filters.pattern_types = [t.strip() for t in pattern_types.split(",")]
    if projects:
        filters.projects = [p.strip() for p in projects.split(",")]

    await manager.connect(websocket, filters)

    try:
        # Send welcome message
        welcome = {
            "type": "connection_established",
            "message": "Successfully connected to UCKN updates",
            "filters": filters.dict() if filters else None,
        }
        import json

        await manager.send_personal_message(json.dumps(welcome), websocket)

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client messages (ping/pong, filter updates, etc.)
                data = await websocket.receive_text()

                # Parse client message
                try:
                    message = json.loads(data)
                    message_type = message.get("type")

                    if message_type == "ping":
                        await manager.send_personal_message(
                            json.dumps(
                                {"type": "pong", "timestamp": "2024-01-01T00:00:00Z"}
                            ),
                            websocket,
                        )
                    elif message_type == "update_filters":
                        # Update connection filters
                        new_filters = UpdateFilter(**message.get("filters", {}))
                        manager.connection_filters[websocket] = new_filters
                        await manager.send_personal_message(
                            json.dumps(
                                {
                                    "type": "filters_updated",
                                    "filters": new_filters.dict(),
                                }
                            ),
                            websocket,
                        )

                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from WebSocket: {data}")

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket connection: {e}")
                break

    finally:
        manager.disconnect(websocket)


# Enhanced Collaboration Endpoints


@router.post(
    "/patterns/{pattern_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_comment(
    pattern_id: str,
    request: CommentRequest,
    collab_manager: CollaborationManager = Depends(get_collaboration_manager),
):
    """Add a comment to a pattern."""
    try:
        # Mock user ID - in real implementation, get from auth
        user_id = "mock_user_id"

        comment = CollabComment(
            pattern_id=pattern_id,
            user_id=user_id,
            parent_id=request.parent_id,
            content=request.content,
            metadata=request.metadata,
        )

        added_comment = await collab_manager.add_comment(comment)

        # Broadcast comment to WebSocket connections
        broadcast_message = {
            "type": "comment_added",
            "pattern_id": pattern_id,
            "comment_id": added_comment.id,
            "user_id": user_id,
            "timestamp": added_comment.created_at.isoformat(),
        }
        await manager.broadcast(json.dumps(broadcast_message))

        return CommentResponse(
            id=added_comment.id,
            pattern_id=added_comment.pattern_id,
            user_id=added_comment.user_id,
            parent_id=added_comment.parent_id,
            content=added_comment.content,
            metadata=added_comment.metadata,
            created_at=added_comment.created_at,
            updated_at=added_comment.updated_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add comment",
        )


@router.get("/patterns/{pattern_id}/comments", response_model=list[CommentResponse])
async def get_comments(
    pattern_id: str,
    parent_id: str | None = None,
    collab_manager: CollaborationManager = Depends(get_collaboration_manager),
):
    """Get comments for a pattern."""
    try:
        comments = await collab_manager.get_comments(pattern_id, parent_id)

        return [
            CommentResponse(
                id=comment.id,
                pattern_id=comment.pattern_id,
                user_id=comment.user_id,
                parent_id=comment.parent_id,
                content=comment.content,
                metadata=comment.metadata,
                created_at=comment.created_at,
                updated_at=comment.updated_at,
            )
            for comment in comments
        ]

    except Exception as e:
        logger.error(f"Error getting comments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get comments",
        )


@router.get("/activity/feed", response_model=list[ActivityEventResponse])
async def get_activity_feed(
    team_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    collab_manager: CollaborationManager = Depends(get_collaboration_manager),
):
    """Get activity feed for a team or user."""
    try:
        activities = await collab_manager.get_activity_feed(
            team_id=team_id, limit=limit
        )

        # Apply offset
        activities = activities[offset : offset + limit]

        return [
            ActivityEventResponse(
                id=activity.id,
                type=activity.type,
                user_id=activity.user_id,
                team_id=activity.team_id,
                resource_id=activity.resource_id,
                resource_type=activity.resource_type,
                action=activity.action,
                metadata=activity.metadata,
                timestamp=activity.timestamp,
            )
            for activity in activities
        ]

    except Exception as e:
        logger.error(f"Error getting activity feed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get activity feed",
        )


@router.post(
    "/notifications/preferences",
    response_model=NotificationPreferenceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def set_notification_preference(
    request: NotificationPreferenceRequest,
    collab_manager: CollaborationManager = Depends(get_collaboration_manager),
):
    """Set notification preferences for the current user."""
    try:
        # Mock user ID - in real implementation, get from auth
        user_id = "mock_user_id"

        preference = NotificationPreference(
            user_id=user_id,
            notification_type=request.notification_type,
            event_types=request.event_types,
            settings=request.settings,
            enabled=request.enabled,
        )

        await collab_manager.set_notification_preference(preference)

        return NotificationPreferenceResponse(
            user_id=preference.user_id,
            notification_type=preference.notification_type,
            event_types=preference.event_types,
            settings=preference.settings,
            enabled=preference.enabled,
        )

    except Exception as e:
        logger.error(f"Error setting notification preference: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set notification preference",
        )


@router.post(
    "/teams/{team_id}/webhooks",
    response_model=WebhookConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_webhook(
    team_id: str,
    request: WebhookConfigRequest,
    collab_manager: CollaborationManager = Depends(get_collaboration_manager),
):
    """Add webhook configuration for a team."""
    try:
        webhook = WebhookConfig(
            team_id=team_id,
            name=request.name,
            url=request.url,
            secret=request.secret,
            event_types=request.event_types,
            enabled=request.enabled,
            settings=request.settings,
        )

        await collab_manager.add_webhook(webhook)

        return WebhookConfigResponse(
            id=webhook.id,
            team_id=webhook.team_id,
            name=webhook.name,
            url=webhook.url,
            event_types=webhook.event_types,
            enabled=webhook.enabled,
            settings=webhook.settings,
            created_at=datetime.now(timezone.utc),
        )

    except Exception as e:
        logger.error(f"Error adding webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add webhook",
        )


@router.post(
    "/teams/{team_id}/libraries",
    response_model=PatternLibraryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_pattern_library(team_id: str, request: PatternLibraryRequest):
    """Create a team-scoped pattern library."""
    try:
        from uuid import uuid4

        library_id = str(uuid4())

        # Mock implementation - in real version, store in database
        return PatternLibraryResponse(
            id=library_id,
            team_id=team_id,
            name=request.name,
            description=request.description,
            pattern_ids=request.pattern_ids,
            settings=request.settings,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    except Exception as e:
        logger.error(f"Error creating pattern library: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create pattern library",
        )


@router.get("/teams/{team_id}/libraries", response_model=list[PatternLibraryResponse])
async def list_pattern_libraries(team_id: str):
    """List pattern libraries for a team."""
    try:
        # Mock implementation
        return [
            PatternLibraryResponse(
                id="lib-1",
                team_id=team_id,
                name="CI/CD Patterns",
                description="Common CI/CD automation patterns",
                pattern_ids=["pattern-1", "pattern-2"],
                settings={"auto_sync": True},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        ]

    except Exception as e:
        logger.error(f"Error listing pattern libraries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list pattern libraries",
        )


@router.websocket("/patterns/{pattern_id}/collaborate")
async def collaborative_editing(websocket: WebSocket, pattern_id: str):
    """WebSocket endpoint for real-time collaborative editing."""
    await websocket.accept()

    try:
        # Send welcome message
        welcome = {
            "type": "edit_session_established",
            "pattern_id": pattern_id,
            "message": "Connected to collaborative editing session",
        }
        await websocket.send_text(json.dumps(welcome))

        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                message_type = message.get("type")

                if message_type == "edit_operation":
                    # Handle collaborative edit operation
                    operation = {
                        "type": "edit_operation_applied",
                        "pattern_id": pattern_id,
                        "operation": message.get("operation"),
                        "user_id": "mock_user_id",  # Get from auth
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }

                    # Broadcast to other collaborators in the same pattern
                    # In real implementation, this would use a room-based broadcasting system
                    await websocket.send_text(json.dumps(operation))

                elif message_type == "cursor_position":
                    # Handle cursor position updates
                    cursor_update = {
                        "type": "cursor_position_update",
                        "pattern_id": pattern_id,
                        "user_id": "mock_user_id",
                        "position": message.get("position"),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    await websocket.send_text(json.dumps(cursor_update))

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                logger.warning(
                    f"Invalid JSON received in collaborative editing: {data}"
                )
            except Exception as e:
                logger.error(f"Error in collaborative editing: {e}")
                break

    finally:
        # Clean up collaborative editing session
        logger.info(f"Collaborative editing session ended for pattern {pattern_id}")
