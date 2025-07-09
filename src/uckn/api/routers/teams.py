"""
Team Management API Router for UCKN.

Provides comprehensive team management endpoints including:
- Team CRUD operations
- Member management
- Role assignment
- Invitation system
"""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ...api.dependencies import get_knowledge_manager
from ...core.organisms.knowledge_manager import KnowledgeManager

router = APIRouter()


# Request/Response Models
class TeamCreateRequest(BaseModel):
    name: str
    description: str | None = None
    settings: dict | None = None


class TeamResponse(BaseModel):
    id: str
    name: str
    description: str | None
    owner_id: str
    settings: dict
    created_at: str
    updated_at: str


class TeamMemberResponse(BaseModel):
    user_id: str
    team_id: str
    role: str
    joined_at: str


class AddMemberRequest(BaseModel):
    user_id: str
    role: str = "reader"


class UpdateMemberRequest(BaseModel):
    role: str


class InvitationRequest(BaseModel):
    email: str
    role: str = "reader"


class InvitationResponse(BaseModel):
    id: str
    team_id: str
    email: str
    role: str
    invited_by: str
    expires_at: str
    status: str


# Team Management Endpoints
@router.post("/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    request: TeamCreateRequest, km: KnowledgeManager = Depends(get_knowledge_manager)
):
    """Create a new team."""
    try:
        # For now, use a mock user ID - in real implementation, get from auth
        owner_id = "mock_user_id"

        team_data = {
            "id": str(uuid4()),
            "name": request.name,
            "description": request.description,
            "owner_id": owner_id,
            "settings": request.settings or {},
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }

        # In real implementation, this would use team_manager to save to database
        return TeamResponse(**team_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create team: {str(e)}",
        )


@router.get("/teams", response_model=list[TeamResponse])
async def list_teams(km: KnowledgeManager = Depends(get_knowledge_manager)):
    """List teams for the current user."""
    try:
        # For now, return mock data - in real implementation, query from database
        mock_teams = [
            {
                "id": "team-1",
                "name": "Development Team",
                "description": "Main development team",
                "owner_id": "mock_user_id",
                "settings": {"pattern_sharing": "team"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        ]

        return [TeamResponse(**team) for team in mock_teams]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list teams: {str(e)}",
        )


@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(team_id: str, km: KnowledgeManager = Depends(get_knowledge_manager)):
    """Get team details."""
    try:
        # Mock implementation - in real version, query database
        if team_id == "team-1":
            team_data = {
                "id": team_id,
                "name": "Development Team",
                "description": "Main development team",
                "owner_id": "mock_user_id",
                "settings": {"pattern_sharing": "team"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
            return TeamResponse(**team_data)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Team not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team: {str(e)}",
        )


@router.get("/teams/{team_id}/members", response_model=list[TeamMemberResponse])
async def list_team_members(
    team_id: str, km: KnowledgeManager = Depends(get_knowledge_manager)
):
    """List team members."""
    try:
        # Mock implementation
        mock_members = [
            {
                "user_id": "user-1",
                "team_id": team_id,
                "role": "admin",
                "joined_at": "2024-01-01T00:00:00Z",
            }
        ]

        return [TeamMemberResponse(**member) for member in mock_members]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list team members: {str(e)}",
        )
