"""
API models for collaboration features.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class CommentRequest(BaseModel):
    """Request model for adding a comment."""
    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CommentResponse(BaseModel):
    """Response model for comments."""
    id: str
    pattern_id: str
    user_id: str
    parent_id: Optional[str]
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]
    replies: Optional[List["CommentResponse"]] = None


class ActivityFeedRequest(BaseModel):
    """Request model for activity feed."""
    team_id: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    event_types: Optional[List[str]] = None


class ActivityEventResponse(BaseModel):
    """Response model for activity events."""
    id: str
    type: str
    user_id: str
    team_id: Optional[str]
    resource_id: Optional[str]
    resource_type: Optional[str]
    action: str
    metadata: Dict[str, Any]
    timestamp: datetime


class NotificationPreferenceRequest(BaseModel):
    """Request model for notification preferences."""
    notification_type: str = Field(..., pattern="^(email|in_app|webhook)$")
    event_types: List[str] = Field(..., min_length=1)
    settings: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class NotificationPreferenceResponse(BaseModel):
    """Response model for notification preferences."""
    user_id: str
    notification_type: str
    event_types: List[str]
    settings: Dict[str, Any]
    enabled: bool


class WebhookConfigRequest(BaseModel):
    """Request model for webhook configuration."""
    name: str = Field(..., min_length=1, max_length=100)
    url: str = Field(..., pattern="^https?://")
    secret: Optional[str] = None
    event_types: List[str] = Field(..., min_length=1)
    enabled: bool = True
    settings: Dict[str, Any] = Field(default_factory=dict)


class WebhookConfigResponse(BaseModel):
    """Response model for webhook configuration."""
    id: str
    team_id: str
    name: str
    url: str
    event_types: List[str]
    enabled: bool
    settings: Dict[str, Any]
    created_at: datetime


class PatternLibraryRequest(BaseModel):
    """Request model for team-scoped pattern library."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    pattern_ids: List[str] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=dict)


class PatternLibraryResponse(BaseModel):
    """Response model for pattern library."""
    id: str
    team_id: str
    name: str
    description: Optional[str]
    pattern_ids: List[str]
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class CollaborativeEditRequest(BaseModel):
    """Request model for collaborative editing operations."""
    operation_type: str = Field(..., pattern="^(insert|delete|retain)$")
    position: int = Field(..., ge=0)
    content: Optional[str] = None
    length: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


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