"""Common Pydantic Models for UCKN API"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base response model with common fields"""
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseResponse):
    """Error response model"""
    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class PaginatedResponse(BaseResponse):
    """Paginated response model"""
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    size: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there are more pages")
    has_prev: bool = Field(description="Whether there are previous pages")
    
    @classmethod
    def create(cls, items: List[Any], total: int, page: int, size: int) -> "PaginatedResponse":
        """Create paginated response from items and pagination info"""
        pages = (total + size - 1) // size
        return cls(
            data=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )


class TechStackFilter(BaseModel):
    """Technology stack filter model"""
    languages: Optional[List[str]] = Field(default=None, description="Programming languages")
    frameworks: Optional[List[str]] = Field(default=None, description="Frameworks")
    libraries: Optional[List[str]] = Field(default=None, description="Libraries")
    tools: Optional[List[str]] = Field(default=None, description="Development tools")
    platforms: Optional[List[str]] = Field(default=None, description="Platforms")
    
    def to_metadata_filter(self) -> Dict[str, Any]:
        """Convert to metadata filter dictionary"""
        filter_dict = {}
        if self.languages:
            filter_dict["technology_stack.languages"] = {"$in": self.languages}
        if self.frameworks:
            filter_dict["technology_stack.frameworks"] = {"$in": self.frameworks}
        if self.libraries:
            filter_dict["technology_stack.libraries"] = {"$in": self.libraries}
        if self.tools:
            filter_dict["technology_stack.tools"] = {"$in": self.tools}
        if self.platforms:
            filter_dict["technology_stack.platforms"] = {"$in": self.platforms}
        return filter_dict


class TechnologyStackDNA(BaseModel):
    """Technology stack DNA model"""
    languages: List[str] = Field(default_factory=list, description="Programming languages detected")
    frameworks: List[str] = Field(default_factory=list, description="Frameworks detected")
    libraries: List[str] = Field(default_factory=list, description="Libraries detected")
    tools: List[str] = Field(default_factory=list, description="Development tools detected")
    platforms: List[str] = Field(default_factory=list, description="Platforms detected")
    build_systems: List[str] = Field(default_factory=list, description="Build systems detected")
    testing_frameworks: List[str] = Field(default_factory=list, description="Testing frameworks detected")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence score of detection")
    analysis_timestamp: datetime = Field(default_factory=datetime.now)


class SearchParams(BaseModel):
    """Common search parameters"""
    query: str = Field(min_length=1, max_length=1000, description="Search query")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    min_similarity: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    metadata_filter: Optional[Dict[str, Any]] = Field(default=None, description="Metadata filter")


class SharingScope(str, Enum):
    """Pattern sharing scope"""
    PRIVATE = "private"
    TEAM = "team"
    ORGANIZATION = "organization"
    PUBLIC = "public"


class UserRole(str, Enum):
    """User roles"""
    VIEWER = "viewer"
    CONTRIBUTOR = "contributor"
    ADMIN = "admin"
    OWNER = "owner"


class ValidationResult(BaseModel):
    """Pattern validation result"""
    is_valid: bool = Field(description="Whether the pattern is valid")
    score: float = Field(ge=0.0, le=1.0, description="Validation score")
    feedback: Optional[str] = Field(default=None, description="Validation feedback")
    issues: List[str] = Field(default_factory=list, description="List of validation issues")
    suggestions: List[str] = Field(default_factory=list, description="List of improvement suggestions")
    validator_id: Optional[str] = Field(default=None, description="ID of the validator")
    validation_timestamp: datetime = Field(default_factory=datetime.now)


class HealthStatus(BaseModel):
    """System health status"""
    status: str = Field(description="Overall system status")
    unified_db_available: bool = Field(description="Whether unified database is available")
    semantic_search_available: bool = Field(description="Whether semantic search is available")
    knowledge_dir: str = Field(description="Knowledge directory path")
    components: Dict[str, str] = Field(description="Component health status")
    uptime: Optional[float] = Field(default=None, description="System uptime in seconds")
    memory_usage: Optional[float] = Field(default=None, description="Memory usage percentage")
    disk_usage: Optional[float] = Field(default=None, description="Disk usage percentage")
    timestamp: datetime = Field(default_factory=datetime.now)


class UpdateFilter(BaseModel):
    """Filter for subscription updates"""
    pattern_types: Optional[List[str]] = Field(default=None, description="Pattern types to subscribe to")
    technologies: Optional[List[str]] = Field(default=None, description="Technologies to subscribe to")
    project_ids: Optional[List[str]] = Field(default=None, description="Project IDs to subscribe to")
    user_ids: Optional[List[str]] = Field(default=None, description="User IDs to subscribe to")
    min_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Minimum pattern score")


class SetupRecommendation(BaseModel):
    """Setup recommendation model"""
    category: str = Field(description="Recommendation category")
    title: str = Field(description="Recommendation title")
    description: str = Field(description="Detailed description")
    priority: str = Field(description="Priority level (high, medium, low)")
    effort: str = Field(description="Estimated effort (high, medium, low)")
    commands: Optional[List[str]] = Field(default=None, description="Commands to execute")
    files_to_create: Optional[List[str]] = Field(default=None, description="Files to create")
    files_to_modify: Optional[List[str]] = Field(default=None, description="Files to modify")
    dependencies: Optional[List[str]] = Field(default=None, description="Dependencies to install")
    references: Optional[List[str]] = Field(default=None, description="Reference links")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in recommendation")


class IssueWarning(BaseModel):
    """Issue warning model"""
    severity: str = Field(description="Issue severity (critical, high, medium, low)")
    category: str = Field(description="Issue category")
    title: str = Field(description="Issue title")
    description: str = Field(description="Detailed description")
    potential_impact: str = Field(description="Potential impact description")
    suggested_actions: List[str] = Field(description="Suggested actions to resolve")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in prediction")
    estimated_probability: float = Field(ge=0.0, le=1.0, description="Estimated probability of occurrence")
    related_patterns: Optional[List[str]] = Field(default=None, description="Related pattern IDs")
