"""Project-related Pydantic Models for UCKN API"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, validator

from .common import (
    BaseResponse,
    IssueWarning,
    SetupRecommendation,
    TechnologyStackDNA,
    UserRole,
)


class ProjectStatus(str, Enum):
    """Project status enumeration"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ProjectType(str, Enum):
    """Project type enumeration"""

    WEB_APPLICATION = "web_application"
    MOBILE_APPLICATION = "mobile_application"
    DESKTOP_APPLICATION = "desktop_application"
    API_SERVICE = "api_service"
    LIBRARY = "library"
    FRAMEWORK = "framework"
    TOOL = "tool"
    SCRIPT = "script"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class ProjectVisibility(str, Enum):
    """Project visibility enumeration"""

    PRIVATE = "private"
    TEAM = "team"
    ORGANIZATION = "organization"
    PUBLIC = "public"


class ProjectMember(BaseModel):
    """Project member model"""

    user_id: str = Field(description="User ID")
    username: str = Field(description="Username")
    role: UserRole = Field(description="User role in project")
    permissions: list[str] = Field(
        default_factory=list, description="Specific permissions"
    )
    joined_at: datetime = Field(description="When user joined the project")
    is_active: bool = Field(
        default=True, description="Whether user is active in project"
    )


class ProjectSettings(BaseModel):
    """Project settings model"""

    auto_analyze: bool = Field(
        default=True, description="Automatically analyze project changes"
    )
    pattern_suggestions: bool = Field(
        default=True, description="Enable pattern suggestions"
    )
    issue_predictions: bool = Field(
        default=True, description="Enable issue predictions"
    )
    collaboration_enabled: bool = Field(
        default=True, description="Enable collaboration features"
    )
    notification_preferences: dict[str, bool] = Field(
        default_factory=lambda: {
            "pattern_matches": True,
            "new_recommendations": True,
            "issue_warnings": True,
            "team_updates": False,
        },
        description="Notification preferences",
    )
    integration_settings: dict[str, Any] = Field(
        default_factory=dict, description="Integration-specific settings"
    )


class ProjectMetrics(BaseModel):
    """Project metrics model"""

    patterns_count: int = Field(default=0, description="Number of patterns in project")
    active_patterns: int = Field(default=0, description="Number of active patterns")
    total_lines_of_code: Optional[int] = Field(
        default=None, description="Total lines of code"
    )
    files_count: Optional[int] = Field(default=None, description="Number of files")
    last_analysis: Optional[datetime] = Field(
        default=None, description="Last analysis timestamp"
    )
    health_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Project health score"
    )
    complexity_score: Optional[float] = Field(
        default=None, ge=0.0, le=10.0, description="Project complexity score"
    )
    maintainability_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Maintainability score"
    )
    test_coverage: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Test coverage percentage"
    )


class ProjectCreate(BaseModel):
    """Project creation model"""

    name: str = Field(min_length=1, max_length=100, description="Project name")
    description: Optional[str] = Field(
        default=None, max_length=2000, description="Project description"
    )
    project_type: ProjectType = Field(
        default=ProjectType.OTHER, description="Type of project"
    )
    visibility: ProjectVisibility = Field(
        default=ProjectVisibility.PRIVATE, description="Project visibility"
    )
    repository_url: Optional[str] = Field(
        default=None, description="Git repository URL"
    )
    project_path: Optional[str] = Field(default=None, description="Local project path")
    tags: list[str] = Field(default_factory=list, description="Project tags")
    settings: ProjectSettings = Field(
        default_factory=ProjectSettings, description="Project settings"
    )

    @validator("name")
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Project name cannot be empty")
        return v.strip()

    @validator("tags")
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        return [tag.lower().strip() for tag in v if tag.strip()]


class Project(BaseModel):
    """Complete project model"""

    id: str = Field(description="Project unique identifier")
    name: str = Field(description="Project name")
    description: Optional[str] = Field(default=None, description="Project description")
    project_type: ProjectType = Field(description="Type of project")
    visibility: ProjectVisibility = Field(description="Project visibility")
    status: ProjectStatus = Field(
        default=ProjectStatus.ACTIVE, description="Project status"
    )
    repository_url: Optional[str] = Field(
        default=None, description="Git repository URL"
    )
    project_path: Optional[str] = Field(default=None, description="Local project path")
    tags: list[str] = Field(default_factory=list, description="Project tags")
    technology_stack: Optional[TechnologyStackDNA] = Field(
        default=None, description="Detected technology stack"
    )
    settings: ProjectSettings = Field(description="Project settings")
    metrics: ProjectMetrics = Field(description="Project metrics")
    members: list[ProjectMember] = Field(
        default_factory=list, description="Project members"
    )
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    created_by: str = Field(description="Creator user ID")
    updated_by: str = Field(description="Last updater user ID")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ProjectUpdate(BaseModel):
    """Project update model"""

    name: Optional[str] = Field(
        default=None, min_length=1, max_length=100, description="Updated name"
    )
    description: Optional[str] = Field(
        default=None, max_length=2000, description="Updated description"
    )
    project_type: Optional[ProjectType] = Field(
        default=None, description="Updated project type"
    )
    visibility: Optional[ProjectVisibility] = Field(
        default=None, description="Updated visibility"
    )
    status: Optional[ProjectStatus] = Field(default=None, description="Updated status")
    repository_url: Optional[str] = Field(
        default=None, description="Updated repository URL"
    )
    project_path: Optional[str] = Field(
        default=None, description="Updated project path"
    )
    tags: Optional[list[str]] = Field(default=None, description="Updated tags")
    settings: Optional[ProjectSettings] = Field(
        default=None, description="Updated settings"
    )

    @validator("tags")
    def validate_tags(cls, v):
        if v is not None and len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        return [tag.lower().strip() for tag in v if tag.strip()] if v else v


class ProjectAnalysisRequest(BaseModel):
    """Project analysis request model"""

    project_path: str = Field(description="Path to project directory")
    deep_analysis: bool = Field(default=False, description="Perform deep analysis")
    include_patterns: bool = Field(
        default=True, description="Include pattern extraction"
    )
    include_issues: bool = Field(default=True, description="Include issue prediction")
    include_recommendations: bool = Field(
        default=True, description="Include setup recommendations"
    )
    exclude_patterns: list[str] = Field(
        default_factory=list, description="File patterns to exclude"
    )

    @validator("project_path")
    def validate_project_path(cls, v):
        if not v.strip():
            raise ValueError("Project path cannot be empty")
        return v.strip()


class ProjectAnalysisResponse(BaseResponse):
    """Project analysis response model"""

    project_id: Optional[str] = Field(default=None, description="Associated project ID")
    technology_stack: TechnologyStackDNA = Field(
        description="Detected technology stack"
    )
    recommendations: list[SetupRecommendation] = Field(
        description="Setup recommendations"
    )
    issue_warnings: list[IssueWarning] = Field(description="Predicted issues")
    patterns_found: int = Field(description="Number of patterns found")
    analysis_duration_ms: float = Field(description="Analysis duration in milliseconds")
    health_score: Optional[float] = Field(
        default=None, description="Project health score"
    )
    complexity_metrics: Optional[dict[str, Any]] = Field(
        default=None, description="Complexity metrics"
    )


class ProjectSearchRequest(BaseModel):
    """Project search request model"""

    query: Optional[str] = Field(default=None, description="Search query")
    project_type: Optional[ProjectType] = Field(
        default=None, description="Filter by project type"
    )
    visibility: Optional[ProjectVisibility] = Field(
        default=None, description="Filter by visibility"
    )
    status: Optional[ProjectStatus] = Field(
        default=None, description="Filter by status"
    )
    tags: Optional[list[str]] = Field(default=None, description="Filter by tags")
    technologies: Optional[list[str]] = Field(
        default=None, description="Filter by technologies"
    )
    created_after: Optional[datetime] = Field(
        default=None, description="Filter by creation date"
    )
    created_before: Optional[datetime] = Field(
        default=None, description="Filter by creation date"
    )
    owner_id: Optional[str] = Field(default=None, description="Filter by owner")
    member_id: Optional[str] = Field(default=None, description="Filter by member")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Results offset")


class ProjectMemberInvite(BaseModel):
    """Project member invite model"""

    user_id: Optional[str] = Field(default=None, description="User ID to invite")
    email: Optional[str] = Field(default=None, description="Email to invite")
    role: UserRole = Field(description="Role to assign")
    permissions: Optional[list[str]] = Field(
        default=None, description="Specific permissions"
    )
    message: Optional[str] = Field(default=None, description="Invitation message")

    @validator("user_id", "email")
    def validate_user_identifier(cls, v, values):
        if not v and not values.get("email"):
            raise ValueError("Either user_id or email must be provided")
        return v


class ProjectMemberUpdate(BaseModel):
    """Project member update model"""

    role: Optional[UserRole] = Field(default=None, description="Updated role")
    permissions: Optional[list[str]] = Field(
        default=None, description="Updated permissions"
    )
    is_active: Optional[bool] = Field(default=None, description="Updated active status")


class ProjectCreateResponse(BaseResponse):
    """Project creation response model"""

    project_id: str = Field(description="Created project ID")
    project: Project = Field(description="Created project data")


class ProjectStatsResponse(BaseResponse):
    """Project statistics response model"""

    total_projects: int = Field(description="Total number of projects")
    active_projects: int = Field(description="Number of active projects")
    projects_by_type: dict[str, int] = Field(description="Projects grouped by type")
    projects_by_visibility: dict[str, int] = Field(
        description="Projects grouped by visibility"
    )
    avg_health_score: Optional[float] = Field(
        default=None, description="Average health score"
    )
    total_patterns: int = Field(description="Total patterns across all projects")
    most_used_technologies: list[dict[str, Any]] = Field(
        description="Most commonly used technologies"
    )
