"""
Pattern management endpoints for UCKN API.
"""

import datetime  # Added for timestamp
import hashlib  # Added for document hash
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ...core.organisms.knowledge_manager import KnowledgeManager
from ..dependencies import get_knowledge_manager
from ..models.common import BaseResponse  # For PatternContributionResponse inheritance
from ..models.patterns import PatternStatus, PatternSubmission

logger = logging.getLogger(__name__)
router = APIRouter()


class TechStackFilter(BaseModel):
    """Technology stack filter for pattern search."""

    technologies: list[str] | None = None
    project_type: str | None = None
    complexity: str | None = None


class PatternSearchRequest(BaseModel):
    """Request model for pattern search."""

    query: str = Field(..., description="Search query string")
    filters: TechStackFilter | None = None
    limit: int = Field(default=10, ge=1, le=100)
    min_similarity: float = Field(default=0.7, ge=0.0, le=1.0)


class PatternSearchResponse(BaseModel):
    """Response model for pattern search."""

    patterns: list[dict[str, Any]]
    total_count: int
    query_time_ms: int


# Updated PatternSubmission model is imported from models/patterns.py
# class PatternSubmission(BaseModel):
#     """Model for pattern contribution."""
#     document: str = Field(..., description="Pattern documentation text")
#     metadata: Dict[str, Any] = Field(default_factory=dict)
#     project_id: Optional[str] = None


# Update PatternContributionResponse to inherit from BaseResponse
class PatternContributionResponse(BaseResponse):
    """Response model for pattern contribution."""

    pattern_id: str
    status: str  # This will be the PatternStatus value
    message: str


class ValidationResult(BaseModel):
    """Model for pattern validation result."""

    success: bool
    feedback: str | None = None
    score: float | None = None


class ValidationResponse(BaseModel):
    """Response model for pattern validation."""

    pattern_id: str
    validation_status: str
    message: str


@router.post("/patterns/search", response_model=PatternSearchResponse)
async def search_patterns(
    request: PatternSearchRequest,
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager),
):
    """Search for knowledge patterns using semantic similarity."""
    try:
        import time

        start_time = time.time()

        # Convert filters to metadata filter
        metadata_filter = None
        if request.filters:
            metadata_filter = {}
            if request.filters.technologies:
                metadata_filter["technology_stack"] = ",".join(
                    request.filters.technologies
                )
            if request.filters.project_type:
                metadata_filter["project_type"] = request.filters.project_type
            if request.filters.complexity:
                metadata_filter["complexity"] = request.filters.complexity

        # Search patterns
        patterns = knowledge_manager.search_patterns(
            query=request.query,
            limit=request.limit,
            min_similarity=request.min_similarity,
            metadata_filter=metadata_filter,
        )

        query_time = int((time.time() - start_time) * 1000)

        return PatternSearchResponse(
            patterns=patterns, total_count=len(patterns), query_time_ms=query_time
        )

    except Exception as e:
        logger.error(f"Error searching patterns: {e}")
        raise HTTPException(
            status_code=500, detail=f"Pattern search failed: {str(e)}"
        ) from e


@router.post("/patterns/contribute", response_model=PatternContributionResponse)
async def contribute_pattern(
    pattern: PatternSubmission,
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager),
):
    """Contribute a new knowledge pattern."""
    try:
        # Add initial status and versioning info
        # Convert Pydantic models within PatternSubmission to dict/value for storage
        pattern_data = {
            "document": pattern.document,
            "metadata": pattern.metadata.dict(),  # Convert metadata Pydantic model to dict
            "project_id": pattern.project_id,
            "sharing_scope": pattern.sharing_scope.value,  # Convert enum to value
            "status": PatternStatus.DRAFT.value,  # Set initial status to DRAFT
            "current_version": "0.1.0",  # Initial version for a new draft
            "versions": [],  # Initialize versions list
            "reviews": [],  # Initialize reviews list
        }

        # Generate initial version entry
        initial_doc_hash = hashlib.sha256(pattern.document.encode("utf-8")).hexdigest()
        initial_version_entry = {
            "version_number": "0.1.0",
            "changes": "Initial draft submission",
            "timestamp": datetime.datetime.now().isoformat(),  # Use isoformat for JSON serialization
            "author_id": "system_or_contributor_id",  # Placeholder, should come from auth system
            "document_hash": initial_doc_hash,
            "status_at_creation": PatternStatus.DRAFT.value,
        }
        pattern_data["versions"].append(initial_version_entry)

        pattern_id = knowledge_manager.add_pattern(pattern_data)

        if pattern_id:
            return PatternContributionResponse(
                success=True,  # From BaseResponse
                pattern_id=pattern_id,
                status=PatternStatus.DRAFT.value,
                message="Pattern contributed successfully as DRAFT",
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to contribute pattern")

    except Exception as e:
        logger.error(f"Error contributing pattern: {e}")
        raise HTTPException(
            status_code=500, detail=f"Pattern contribution failed: {str(e)}"
        ) from e


@router.put("/patterns/{pattern_id}/validate", response_model=ValidationResponse)
async def validate_pattern(
    pattern_id: str,
    validation: ValidationResult,
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager),
):
    """Validate a pattern with feedback."""
    try:
        # Get the pattern first to verify it exists
        pattern = knowledge_manager.get_pattern(pattern_id)
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")

        # Update pattern with validation feedback
        updates = {
            "metadata": {
                **pattern.get("metadata", {}),
                "validated": validation.success,
                "validation_feedback": validation.feedback,
                "validation_score": validation.score,
            }
        }

        success = knowledge_manager.update_pattern(pattern_id, updates)

        if success:
            return ValidationResponse(
                pattern_id=pattern_id,
                validation_status="completed",
                message="Pattern validation recorded successfully",
            )
        else:
            raise HTTPException(
                status_code=400, detail="Failed to update pattern validation"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating pattern: {e}")
        raise HTTPException(
            status_code=500, detail=f"Pattern validation failed: {str(e)}"
        ) from e
