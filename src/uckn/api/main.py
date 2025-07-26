"""
UCKN FastAPI Main Application
Implements comprehensive API endpoints for knowledge access and pattern management.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..core.organisms.knowledge_manager import KnowledgeManager
from .dependencies import set_knowledge_manager, get_knowledge_manager
from .routers import (
    auth,
    collaboration,
    health,
    patterns,
    predictions,
    projects,
    teams,
    workflow,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting UCKN FastAPI server...")
    try:
        knowledge_manager = KnowledgeManager()
        set_knowledge_manager(knowledge_manager)
        logger.info("Knowledge manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize knowledge manager: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down UCKN FastAPI server...")


# Create FastAPI application
app = FastAPI(
    title="Universal Claude Code Knowledge Network (UCKN) API",
    description="RESTful API for AI-powered development knowledge management",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": "internal_error"},
    )


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(teams.router, prefix="/api/v1", tags=["Teams"])
app.include_router(predictions.router, prefix="/api/v1", tags=["Predictions"])
app.include_router(patterns.router, prefix="/api/v1", tags=["Patterns"])
app.include_router(workflow.router, prefix="/api/v1", tags=["Workflow"])
app.include_router(projects.router, prefix="/api/v1", tags=["Projects"])
app.include_router(collaboration.router, prefix="/api/v1", tags=["Collaboration"])


# Export for dependency injection
__all__ = ["app"]
