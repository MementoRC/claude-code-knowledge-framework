"""
Pattern management endpoints for UCKN API.
"""

import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ...core.organisms.knowledge_manager import KnowledgeManager
from ..dependencies import get_knowledge_manager

logger = logging.getLogger(__name__)
router = APIRouter()


class TechStackFilter(BaseModel):
    """Technology stack filter for pattern search."""
    technologies: Optional[List[str]] = None
    project_type: Optional[str] = None
    complexity: Optional[str] = None


class PatternSearchRequest(BaseModel):
    """Request model for pattern search."""
    query: str = Field(..., description="Search query string")
    filters: Optional[TechStackFilter] = None
    limit: int = Field(default=10, ge=1, le=100)
    min_similarity: float = Field(default=0.7, ge=0.0, le=1.0)


class PatternSearchResponse(BaseModel):
    """Response model for pattern search."""
    patterns: List[Dict[str, Any]]
    total_count: int
    query_time_ms: int


class PatternSubmission(BaseModel):
    """Model for pattern contribution."""
    document: str = Field(..., description="Pattern documentation text")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    project_id: Optional[str] = None


class PatternContributionResponse(BaseModel):
    """Response model for pattern contribution."""
    pattern_id: str
    status: str
    message: str


class ValidationResult(BaseModel):
    """Model for pattern validation result."""
    success: bool
    feedback: Optional[str] = None
    score: Optional[float] = None


class ValidationResponse(BaseModel):
    """Response model for pattern validation."""
    pattern_id: str
    validation_status: str
    message: str


@router.post("/patterns/search", response_model=PatternSearchResponse)
async def search_patterns(
    request: PatternSearchRequest,
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
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
                metadata_filter["technology_stack"] = ",".join(request.filters.technologies)
            if request.filters.project_type:
                metadata_filter["project_type"] = request.filters.project_type
            if request.filters.complexity:
                metadata_filter["complexity"] = request.filters.complexity
        
        # Search patterns
        patterns = knowledge_manager.search_patterns(
            query=request.query,
            limit=request.limit,
            min_similarity=request.min_similarity,
            metadata_filter=metadata_filter
        )
        
        query_time = int((time.time() - start_time) * 1000)
        
        return PatternSearchResponse(
            patterns=patterns,
            total_count=len(patterns),
            query_time_ms=query_time
        )
        
    except Exception as e:
        logger.error(f"Error searching patterns: {e}")
        raise HTTPException(status_code=500, detail=f"Pattern search failed: {str(e)}")


@router.post("/patterns/contribute", response_model=PatternContributionResponse)
async def contribute_pattern(
    pattern: PatternSubmission,
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """Contribute a new knowledge pattern."""
    try:
        pattern_data = {
            "document": pattern.document,
            "metadata": pattern.metadata,
            "project_id": pattern.project_id
        }
        
        pattern_id = knowledge_manager.add_pattern(pattern_data)
        
        if pattern_id:
            return PatternContributionResponse(
                pattern_id=pattern_id,
                status="success",
                message="Pattern contributed successfully"
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to contribute pattern")
            
    except Exception as e:
        logger.error(f"Error contributing pattern: {e}")
        raise HTTPException(status_code=500, detail=f"Pattern contribution failed: {str(e)}")


@router.put("/patterns/{pattern_id}/validate", response_model=ValidationResponse)
async def validate_pattern(
    pattern_id: str,
    validation: ValidationResult,
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
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
                "validation_score": validation.score
            }
        }
        
        success = knowledge_manager.update_pattern(pattern_id, updates)
        
        if success:
            return ValidationResponse(
                pattern_id=pattern_id,
                validation_status="completed",
                message="Pattern validation recorded successfully"
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to update pattern validation")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating pattern: {e}")
        raise HTTPException(status_code=500, detail=f"Pattern validation failed: {str(e)}")