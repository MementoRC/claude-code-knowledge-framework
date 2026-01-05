"""
MCP Session Manager for UCKN - Maps MCP session IDs to knowledge sessions.

The MCP protocol uses MCP-Session-Id headers for stateful communication.
This manager:
1. Tracks MCP session IDs from the initialize handshake
2. Maps them to internal knowledge engine sessions
3. Handles session lifecycle (creation, resume, cleanup)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class MCPSessionManager:
    """Manages MCP session IDs and their mapping to knowledge sessions."""

    def __init__(self) -> None:
        self._active_sessions: dict[str, dict[str, Any]] = {}

    async def create_mcp_session(
        self, client_info: dict[str, Any] | None = None
    ) -> str:
        """Create a new MCP session."""
        mcp_session_id = f"uckn-{uuid.uuid4().hex[:16]}"
        now = datetime.now(timezone.utc).isoformat()

        session_data = {
            "mcp_session_id": mcp_session_id,
            "project_path": None,
            "created_at": now,
            "last_activity": now,
            "client_info": client_info or {},
        }

        self._active_sessions[mcp_session_id] = session_data
        logger.info(f"Created MCP session: {mcp_session_id}")
        return mcp_session_id

    async def update_activity(self, mcp_session_id: str) -> None:
        """Update last activity timestamp for session keepalive."""
        now = datetime.now(timezone.utc).isoformat()

        if mcp_session_id in self._active_sessions:
            self._active_sessions[mcp_session_id]["last_activity"] = now

    async def validate_session(self, mcp_session_id: str) -> bool:
        """Validate that an MCP session exists and is active."""
        return mcp_session_id in self._active_sessions

    async def get_session_info(self, mcp_session_id: str) -> dict[str, Any] | None:
        """Get full session information."""
        if mcp_session_id in self._active_sessions:
            return self._active_sessions[mcp_session_id].copy()
        return None

    async def set_project_path(self, mcp_session_id: str, project_path: str) -> None:
        """Associate a project path with an MCP session."""
        if mcp_session_id in self._active_sessions:
            self._active_sessions[mcp_session_id]["project_path"] = project_path

    def get_active_session_count(self) -> int:
        """Get count of active sessions in memory."""
        return len(self._active_sessions)

    async def cleanup_inactive_sessions(self, max_age_seconds: int = 3600) -> int:
        """Clean up inactive sessions from memory cache."""
        now = datetime.now(timezone.utc)
        to_remove = []

        for session_id, session_data in self._active_sessions.items():
            last_activity = datetime.fromisoformat(session_data["last_activity"])
            age = (now - last_activity).total_seconds()
            if age > max_age_seconds:
                to_remove.append(session_id)

        for session_id in to_remove:
            del self._active_sessions[session_id]

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} inactive MCP sessions")

        return len(to_remove)
