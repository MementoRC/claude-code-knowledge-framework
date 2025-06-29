"""
Collaboration endpoints for UCKN API.
"""

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from ...core.organisms.knowledge_manager import KnowledgeManager
from ..dependencies import get_knowledge_manager

logger = logging.getLogger(__name__)
router = APIRouter()


class SharingScope(BaseModel):
    """Sharing scope model."""
    scope_type: str = Field(..., description="Type of sharing scope (public, team, private)")
    team_id: Optional[str] = None
    users: Optional[List[str]] = None


class PatternShareRequest(BaseModel):
    """Request model for pattern sharing."""
    scope: SharingScope
    message: Optional[str] = None


class PatternShareResponse(BaseModel):
    """Response model for pattern sharing."""
    pattern_id: str
    shared_with: str
    share_id: str
    message: str


class UpdateFilter(BaseModel):
    """Update filter model for WebSocket subscriptions."""
    pattern_types: Optional[List[str]] = None
    technologies: Optional[List[str]] = None
    projects: Optional[List[str]] = None


class ConnectionManager:
    """WebSocket connection manager."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_filters: Dict[WebSocket, UpdateFilter] = {}
    
    async def connect(self, websocket: WebSocket, filters: Optional[UpdateFilter] = None):
        """Accept WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        if filters:
            self.connection_filters[websocket] = filters
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_filters:
            del self.connection_filters[websocket]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific WebSocket connection."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message to WebSocket: {e}")
    
    async def broadcast(self, message: str, filters: Optional[UpdateFilter] = None):
        """Broadcast message to all connections matching filters."""
        for connection in self.active_connections:
            # Check if connection matches filter criteria
            if filters and connection in self.connection_filters:
                conn_filter = self.connection_filters[connection]
                # Simple filter matching logic (can be enhanced)
                if not self._matches_filter(filters, conn_filter):
                    continue
            
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                # Remove broken connections
                self.disconnect(connection)
    
    def _matches_filter(self, message_filter: UpdateFilter, conn_filter: UpdateFilter) -> bool:
        """Check if message filter matches connection filter."""
        # Simple implementation - can be enhanced
        if conn_filter.technologies and message_filter.technologies:
            return bool(set(conn_filter.technologies) & set(message_filter.technologies))
        return True


# Global connection manager
manager = ConnectionManager()


@router.post("/patterns/{pattern_id}/share", response_model=PatternShareResponse)
async def share_pattern(
    pattern_id: str,
    request: PatternShareRequest,
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """Share a pattern with specified scope."""
    try:
        # Verify pattern exists
        pattern = knowledge_manager.get_pattern(pattern_id)
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        # Generate share ID (in real implementation, this would be stored in database)
        import uuid
        share_id = str(uuid.uuid4())
        
        # Determine sharing scope description
        if request.scope.scope_type == "public":
            shared_with = "public"
        elif request.scope.scope_type == "team" and request.scope.team_id:
            shared_with = f"team:{request.scope.team_id}"
        elif request.scope.scope_type == "private" and request.scope.users:
            shared_with = f"users:{','.join(request.scope.users)}"
        else:
            raise HTTPException(status_code=400, detail="Invalid sharing scope")
        
        # In a real implementation, store sharing info in database
        # For now, just return success response
        
        # Broadcast update to WebSocket connections
        update_message = {
            "type": "pattern_shared",
            "pattern_id": pattern_id,
            "shared_with": shared_with,
            "timestamp": "2024-01-01T00:00:00Z"  # Should use actual timestamp
        }
        
        import json
        await manager.broadcast(json.dumps(update_message))
        
        return PatternShareResponse(
            pattern_id=pattern_id,
            shared_with=shared_with,
            share_id=share_id,
            message=f"Pattern shared successfully with {shared_with}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sharing pattern: {e}")
        raise HTTPException(status_code=500, detail=f"Pattern sharing failed: {str(e)}")


@router.websocket("/updates/subscribe")
async def subscribe_to_updates(
    websocket: WebSocket,
    technologies: Optional[str] = None,
    pattern_types: Optional[str] = None,
    projects: Optional[str] = None
):
    """WebSocket endpoint for real-time updates subscription."""
    # Parse query parameters into filters
    filters = UpdateFilter()
    if technologies:
        filters.technologies = [t.strip() for t in technologies.split(",")]
    if pattern_types:
        filters.pattern_types = [t.strip() for t in pattern_types.split(",")]
    if projects:
        filters.projects = [p.strip() for p in projects.split(",")]
    
    await manager.connect(websocket, filters)
    
    try:
        # Send welcome message
        welcome = {
            "type": "connection_established",
            "message": "Successfully connected to UCKN updates",
            "filters": filters.dict() if filters else None
        }
        import json
        await manager.send_personal_message(json.dumps(welcome), websocket)
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client messages (ping/pong, filter updates, etc.)
                data = await websocket.receive_text()
                
                # Parse client message
                try:
                    message = json.loads(data)
                    message_type = message.get("type")
                    
                    if message_type == "ping":
                        await manager.send_personal_message(
                            json.dumps({"type": "pong", "timestamp": "2024-01-01T00:00:00Z"}),
                            websocket
                        )
                    elif message_type == "update_filters":
                        # Update connection filters
                        new_filters = UpdateFilter(**message.get("filters", {}))
                        manager.connection_filters[websocket] = new_filters
                        await manager.send_personal_message(
                            json.dumps({"type": "filters_updated", "filters": new_filters.dict()}),
                            websocket
                        )
                    
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from WebSocket: {data}")
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket connection: {e}")
                break
    
    finally:
        manager.disconnect(websocket)