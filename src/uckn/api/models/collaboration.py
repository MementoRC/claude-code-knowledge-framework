"""
API models for collaboration features.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CommentRequest(BaseModel):
    """Request model for adding a comment."""

    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CommentResponse(BaseModel):
    """Response model for comments."""

    id: str
    pattern_id: str
    user_id: str
    parent_id: Optional[str]
    content: str
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]
    replies: Optional[list["CommentResponse"]] = None


class ActivityFeedRequest(BaseModel):
    """Request model for activity feed."""

    team_id: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    event_types: Optional[list[str]] = None


class ActivityEventResponse(BaseModel):
    """Response model for activity events."""

    id: str
    type: str
    user_id: str
    team_id: Optional[str]
    resource_id: Optional[str]
    resource_type: Optional[str]
    action: str
    metadata: dict[str, Any]
    timestamp: datetime


class NotificationPreferenceRequest(BaseModel):
    """Request model for notification preferences."""

    notification_type: str = Field(..., pattern="^(email|in_app|webhook)$")
    event_types: list[str] = Field(..., min_length=1)
    settings: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class NotificationPreferenceResponse(BaseModel):
    """Response model for notification preferences."""

    user_id: str
    notification_type: str
    event_types: list[str]
    settings: dict[str, Any]
    enabled: bool


class WebhookConfigRequest(BaseModel):
    """Request model for webhook configuration."""

    name: str = Field(..., min_length=1, max_length=100)
    url: str = Field(..., pattern="^https?://")
    secret: Optional[str] = None
    event_types: list[str] = Field(..., min_length=1)
    enabled: bool = True
    settings: dict[str, Any] = Field(default_factory=dict)


class WebhookConfigResponse(BaseModel):
    """Response model for webhook configuration."""

    id: str
    team_id: str
    name: str
    url: str
    event_types: list[str]
    enabled: bool
    settings: dict[str, Any]
    created_at: datetime


class PatternLibraryRequest(BaseModel):
    """Request model for team-scoped pattern library."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    pattern_ids: list[str] = Field(default_factory=list)
    settings: dict[str, Any] = Field(default_factory=dict)


class PatternLibraryResponse(BaseModel):
    """Response model for pattern library."""

    id: str
    team_id: str
    name: str
    description: Optional[str]
    pattern_ids: list[str]
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class CollaborativeEditRequest(BaseModel):
    """Request model for collaborative editing operations."""

    operation_type: str = Field(..., pattern="^(insert|delete|retain)$")
    position: int = Field(..., ge=0)
    content: Optional[str] = None
    length: Optional[int] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CollaborativeEditResponse(BaseModel):
    """Response model for collaborative editing."""

    operation_id: str
    pattern_id: str
    user_id: str
    operation_type: str
    position: int
    content: Optional[str]
    length: Optional[int]
    timestamp: datetime
    applied: bool


# Update CommentResponse to handle recursive replies
CommentResponse.model_rebuild()
