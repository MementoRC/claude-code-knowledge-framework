"""
Authentication API Router for UCKN.

Provides authentication and authorization endpoints including:
- API key authentication
- OAuth integration (GitHub, GitLab, Azure DevOps)
- User management
- Permission management
"""

from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ...api.dependencies import get_knowledge_manager
from ...core.organisms.knowledge_manager import KnowledgeManager

router = APIRouter()


# Request/Response Models
class LoginRequest(BaseModel):
    api_key: str


class OAuthRequest(BaseModel):
    code: str
    state: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    oauth_provider: Optional[str]
    roles: list[str]
    permissions: list[str]
    created_at: str
    last_login: Optional[str]


class APIKeyCreateRequest(BaseModel):
    name: str
    permissions: list[str] | None = []
    expires_at: Optional[str] = None


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key: str
    permissions: list[str]
    expires_at: Optional[str]
    created_at: str
    last_used: Optional[str]


class PermissionResponse(BaseModel):
    resource: str
    action: str
    scope: str


# Authentication Endpoints
@router.post("/auth/login", response_model=TokenResponse)
async def login_with_api_key(
    request: LoginRequest, km: KnowledgeManager = Depends(get_knowledge_manager)
):
    """Authenticate with API key and return JWT token."""
    try:
        # Mock implementation - in real version, validate API key against database
        if request.api_key == "test-api-key":
            token_data = {
                "access_token": "mock_jwt_token_" + str(uuid4()),
                "token_type": "bearer",
                "expires_in": 3600,
            }
            return TokenResponse(**token_data)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}",
        ) from e


@router.post("/auth/oauth/{provider}", response_model=TokenResponse)
async def oauth_login(
    provider: str,
    request: OAuthRequest,
    km: KnowledgeManager = Depends(get_knowledge_manager),
):
    """OAuth login with supported providers (github, gitlab, azure-devops)."""
    try:
        # Validate provider
        supported_providers = ["github", "gitlab", "azure-devops"]
        if provider not in supported_providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider. Supported: {supported_providers}",
            )

        # Mock implementation - in real version, exchange code for token with provider
        token_data = {
            "access_token": f"oauth_{provider}_token_" + str(uuid4()),
            "token_type": "bearer",
            "expires_in": 3600,
        }

        return TokenResponse(**token_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth login failed: {str(e)}",
        ) from e


@router.post("/auth/token/refresh", response_model=TokenResponse)
async def refresh_token(km: KnowledgeManager = Depends(get_knowledge_manager)):
    """Refresh OAuth token."""
    try:
        # Mock implementation - in real version, refresh using stored refresh token
        token_data = {
            "access_token": "refreshed_token_" + str(uuid4()),
            "token_type": "bearer",
            "expires_in": 3600,
        }

        return TokenResponse(**token_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}",
        ) from e


# User Management
@router.get("/auth/me", response_model=UserResponse)
async def get_current_user(km: KnowledgeManager = Depends(get_knowledge_manager)):
    """Get current user information."""
    try:
        # Mock implementation - in real version, get from JWT token or API key
        user_data = {
            "id": "user-1",
            "email": "user@example.com",
            "name": "Test User",
            "oauth_provider": "github",
            "roles": ["contributor", "team_member"],
            "permissions": ["read:patterns", "write:patterns", "read:teams"],
            "created_at": "2024-01-01T00:00:00Z",
            "last_login": "2024-01-01T12:00:00Z",
        }

        return UserResponse(**user_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user info: {str(e)}",
        ) from e


@router.get("/auth/permissions", response_model=list[PermissionResponse])
async def get_user_permissions(km: KnowledgeManager = Depends(get_knowledge_manager)):
    """Get current user's permissions."""
    try:
        # Mock implementation
        mock_permissions = [
            {"resource": "patterns", "action": "read", "scope": "all"},
            {"resource": "patterns", "action": "write", "scope": "team"},
            {"resource": "teams", "action": "read", "scope": "member"},
        ]

        return [PermissionResponse(**perm) for perm in mock_permissions]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get permissions: {str(e)}",
        ) from e


# API Key Management
@router.post(
    "/auth/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED
)
async def create_api_key(
    request: APIKeyCreateRequest, km: KnowledgeManager = Depends(get_knowledge_manager)
):
    """Create a new API key."""
    try:
        # Mock implementation - in real version, generate secure key and save to database
        api_key_data = {
            "id": str(uuid4()),
            "name": request.name,
            "key": "uckn_" + str(uuid4()).replace("-", ""),
            "permissions": request.permissions or [],
            "expires_at": request.expires_at,
            "created_at": "2024-01-01T00:00:00Z",
            "last_used": None,
        }

        return APIKeyResponse(**api_key_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}",
        ) from e


@router.get("/auth/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(km: KnowledgeManager = Depends(get_knowledge_manager)):
    """List user's API keys."""
    try:
        # Mock implementation
        mock_keys = [
            {
                "id": "key-1",
                "name": "Development Key",
                "key": "uckn_dev_key_redacted",
                "permissions": ["read:patterns", "write:patterns"],
                "expires_at": "2025-01-01T00:00:00Z",
                "created_at": "2024-01-01T00:00:00Z",
                "last_used": "2024-01-01T12:00:00Z",
            }
        ]

        return [APIKeyResponse(**key) for key in mock_keys]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list API keys: {str(e)}",
        ) from e


@router.delete("/auth/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str, km: KnowledgeManager = Depends(get_knowledge_manager)
):
    """Revoke an API key."""
    try:
        # Mock implementation - in real version, mark key as inactive in database
        pass

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke API key: {str(e)}",
        ) from e
