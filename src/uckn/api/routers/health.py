"""
Health monitoring endpoints for UCKN API.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ...core.organisms.knowledge_manager import KnowledgeManager
from ..dependencies import get_knowledge_manager

logger = logging.getLogger(__name__)
router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    message: str


class SystemStatusResponse(BaseModel):
    """Detailed system status response model."""
    status: str
    components: Dict[str, Any]
    uptime: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="UCKN API is running"
    )


@router.get("/api/v1/status", response_model=SystemStatusResponse)
async def system_status(
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """Detailed system status with component health."""
    try:
        # Get health status from knowledge manager
        health_status = knowledge_manager.get_health_status()
        
        return SystemStatusResponse(
            status="healthy" if health_status.get("unified_db_available") else "degraded",
            components=health_status.get("components", {}),
            uptime="Unknown",  # Could implement actual uptime tracking
            version="1.0.0"
        )
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return SystemStatusResponse(
            status="unhealthy",
            components={},
            uptime="Unknown",
            version="1.0.0"
        )