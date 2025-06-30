"""Pattern-related Pydantic Models for UCKN API"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from .common import BaseResponse, TechnologyStackDNA, ValidationResult, SharingScope
from .workflow import PatternVersion, ReviewFeedback # New import

class PatternType(str, Enum):
    """Pattern type enumeration"""
    CODE_SNIPPET = "code_snippet"
    ARCHITECTURE = "architecture"
    CONFIGURATION = "configuration"
    DEPLOYMENT = "deployment"
    TESTING = "testing"
    DEBUGGING = "debugging"
    OPTIMIZATION = "optimization"
    SECURITY = "security"
    INTEGRATION = "integration"
    WORKFLOW = "workflow"


class PatternPriority(str, Enum):
    """Pattern priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PatternStatus(str, Enum):
    """Pattern status enumeration"""
    DRAFT = "draft"
    IN_REVIEW = "in_review" # New workflow state
    IN_TESTING = "in_testing" # New workflow state
    APPROVED_FOR_PUBLISH = "approved_for_publish" # New workflow state, replaces 'APPROVED'
    PUBLISHED = "published" # New workflow state
    MAINTENANCE = "maintenance" # New workflow state
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


class PatternMetadata(BaseModel):
    """Pattern metadata model"""
    title: str = Field(min_length=1, max_length=200, description="Pattern title")
    description: str = Field(min_length=1, max_length=2000, description="Pattern description")
    pattern_type: PatternType = Field(description="Type of pattern")
    technology_stack: TechnologyStackDNA = Field(description="Technology stack information")
    tags: List[str] = Field(default_factory=list, description="Pattern tags")
    author: Optional[str] = Field(default=None, description="Pattern author")
    version: str = Field(default="1.0.0", description="Pattern version")
    success_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Success rate")
    usage_count: int = Field(default=0, ge=0, description="Number of times used")
    priority: PatternPriority = Field(default=PatternPriority.MEDIUM, description="Pattern priority")
    complexity: int = Field(default=1, ge=1, le=10, description="Pattern complexity (1-10)")
    estimated_time: Optional[int] = Field(default=None, description="Estimated implementation time in minutes")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites")
    related_patterns: List[str] = Field(default_factory=list, description="Related pattern IDs")
    external_links: List[str] = Field(default_factory=list, description="External reference links")
    
    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")
        return [tag.lower().strip() for tag in v if tag.strip()]


class PatternSubmission(BaseModel):
    """Pattern submission model for creating new patterns"""
    document: str = Field(min_length=10, max_length=50000, description="Pattern content/code")
    metadata: PatternMetadata = Field(description="Pattern metadata")
    project_id: Optional[str] = Field(default=None, description="Associated project ID")
    sharing_scope: SharingScope = Field(default=SharingScope.PRIVATE, description="Sharing scope")
    
    @validator('document')
    def validate_document(cls, v):
        if not v.strip():
            raise ValueError("Document content cannot be empty")
        return v.strip()


class Pattern(BaseModel):
    """Complete pattern model with all fields"""
    id: str = Field(description="Pattern unique identifier")
    document: str = Field(description="Pattern content/code")
    metadata: PatternMetadata = Field(description="Pattern metadata")
    project_id: Optional[str] = Field(default=None, description="Associated project ID")
    sharing_scope: SharingScope = Field(default=SharingScope.PRIVATE, description="Sharing scope")
    status: PatternStatus = Field(default=PatternStatus.DRAFT, description="Pattern status")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    created_by: Optional[str] = Field(default=None, description="Creator user ID")
    updated_by: Optional[str] = Field(default=None, description="Last updater user ID")
    embedding: Optional[List[float]] = Field(default=None, description="Semantic embedding vector")
    validation_results: List[ValidationResult] = Field(default_factory=list, description="Validation results")
    
    # New fields for workflow management
    current_version: str = Field(default="1.0.0", description="Current active version of the pattern")
    versions: List[PatternVersion] = Field(default_factory=list, description="History of pattern versions")
    reviews: List[ReviewFeedback] = Field(default_factory=list, description="List of review feedback entries")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PatternSearchResult(BaseModel):
    """Pattern search result with similarity score"""
    pattern: Pattern = Field(description="Pattern data")
    similarity_score: float = Field(ge=0.0, le=1.0, description="Similarity score")
    match_highlights: Optional[List[str]] = Field(default=None, description="Highlighted matching text")
    relevance_factors: Optional[Dict[str, float]] = Field(default=None, description="Factors contributing to relevance")


class PatternSearchRequest(BaseModel):
    """Pattern search request model"""
    query: str = Field(min_length=1, max_length=1000, description="Search query")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Search filters")
    tech_stack_filter: Optional[Dict[str, List[str]]] = Field(default=None, description="Technology stack filters")
    pattern_types: Optional[List[PatternType]] = Field(default=None, description="Pattern types to search")
    tags: Optional[List[str]] = Field(default=None, description="Tags to filter by")
    min_success_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Minimum success rate")
    max_complexity: Optional[int] = Field(default=None, ge=1, le=10, description="Maximum complexity")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results")
    min_similarity: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity threshold")
    include_deprecated: bool = Field(default=False, description="Include deprecated patterns")
    project_id: Optional[str] = Field(default=None, description="Filter by project ID")
    
    def to_metadata_filter(self) -> Dict[str, Any]:
        """Convert search request to metadata filter"""
        filters = {}
        
        if self.pattern_types:
            filters["pattern_type"] = {"$in": [pt.value for pt in self.pattern_types]}
        
        if self.tags:
            filters["tags"] = {"$in": self.tags}
        
        if self.min_success_rate is not None:
            filters["success_rate"] = {"$gte": self.min_success_rate}
        
        if self.max_complexity is not None:
            filters["complexity"] = {"$lte": self.max_complexity}
        
        if not self.include_deprecated:
            filters["status"] = {"$ne": PatternStatus.DEPRECATED.value}
        
        if self.project_id:
            filters["project_id"] = self.project_id
        
        if self.tech_stack_filter:
            for key, values in self.tech_stack_filter.items():
                if values:
                    filters[f"technology_stack.{key}"] = {"$in": values}
        
        # Merge with custom filters
        if self.filters:
            filters.update(self.filters)
        
        return filters


class PatternSearchResponse(BaseResponse):
    """Pattern search response model"""
    results: List[PatternSearchResult] = Field(description="Search results")
    total_count: int = Field(description="Total number of matching patterns")
    search_time_ms: float = Field(description="Search execution time in milliseconds")
    filters_applied: Dict[str, Any] = Field(description="Filters that were applied")


class PatternValidationRequest(BaseModel):
    """Pattern validation request model"""
    pattern_id: str = Field(description="Pattern ID to validate")
    validation_type: str = Field(default="comprehensive", description="Type of validation to perform")
    additional_context: Optional[Dict[str, Any]] = Field(default=None, description="Additional validation context")


class PatternID(BaseModel):
    """Pattern ID response model"""
    pattern_id: str = Field(description="Generated pattern ID")


class PatternCreateResponse(BaseResponse):
    """Pattern creation response model"""
    pattern_id: str = Field(description="Created pattern ID")
    pattern: Pattern = Field(description="Created pattern data")


class PatternUpdateRequest(BaseModel):
    """Pattern update request model"""
    document: Optional[str] = Field(default=None, description="Updated pattern content")
    metadata: Optional[PatternMetadata] = Field(default=None, description="Updated metadata")
    sharing_scope: Optional[SharingScope] = Field(default=None, description="Updated sharing scope")
    status: Optional[PatternStatus] = Field(default=None, description="Updated status")


class PatternBulkOperationRequest(BaseModel):
    """Bulk pattern operation request"""
    pattern_ids: List[str] = Field(min_items=1, max_items=100, description="Pattern IDs")
    operation: str = Field(description="Operation to perform (delete, update_status, etc.)")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Operation parameters")


class PatternAnalytics(BaseModel):
    """Pattern analytics model"""
    pattern_id: str = Field(description="Pattern ID")
    usage_count: int = Field(description="Number of times used")
    success_rate: float = Field(ge=0.0, le=1.0, description="Success rate")
    avg_rating: Optional[float] = Field(default=None, ge=0.0, le=5.0, description="Average user rating")
    feedback_count: int = Field(default=0, description="Number of feedback entries")
    last_used: Optional[datetime] = Field(default=None, description="Last usage timestamp")
    trending_score: float = Field(default=0.0, description="Trending score")
    similar_patterns_count: int = Field(default=0, description="Number of similar patterns")
