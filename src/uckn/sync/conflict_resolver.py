"""
UCKN Conflict Resolution System
Handles conflict detection and resolution for pattern synchronization.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ConflictType(Enum):
    """Types of synchronization conflicts."""

    CONCURRENT_EDIT = "concurrent_edit"
    VERSION_MISMATCH = "version_mismatch"
    SCHEMA_CONFLICT = "schema_conflict"
    CONTENT_CONFLICT = "content_conflict"


class ResolutionStrategy(Enum):
    """Conflict resolution strategies."""

    LOCAL_WINS = "local_wins"
    SERVER_WINS = "server_wins"
    MERGE = "merge"
    MANUAL = "manual"
    NEWEST_WINS = "newest_wins"


class ConflictResolver:
    """
    Handles conflict detection and resolution for pattern synchronization.

    Features:
    - Vector clock-based conflict detection
    - Multiple resolution strategies
    - Content-aware merging
    - Interactive conflict resolution
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.default_strategy = ResolutionStrategy.MANUAL

    def detect_conflict(
        self, local_pattern: dict[str, Any], server_pattern: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        Detect conflicts between local and server patterns.

        Args:
            local_pattern: Local version of the pattern
            server_pattern: Server version of the pattern

        Returns:
            Conflict description if conflict detected, None otherwise
        """
        if not local_pattern or not server_pattern:
            return None

        # Check vector clocks
        local_clock = local_pattern.get("vector_clock", {})
        server_clock = server_pattern.get("vector_clock", {})

        if self._is_concurrent_modification(local_clock, server_clock):
            conflict_type = self._determine_conflict_type(local_pattern, server_pattern)

            return {
                "type": conflict_type.value,
                "pattern_id": local_pattern.get("id"),
                "local_version": local_pattern,
                "server_version": server_pattern,
                "local_clock": local_clock,
                "server_clock": server_clock,
                "detected_at": datetime.now().isoformat(),
            }

        return None

    def _is_concurrent_modification(
        self, clock1: dict[str, int], clock2: dict[str, int]
    ) -> bool:
        """Check if two vector clocks indicate concurrent modifications."""
        # Two clocks are concurrent if neither dominates the other
        clock1_dominates = all(clock1.get(k, 0) >= v for k, v in clock2.items())
        clock2_dominates = all(clock2.get(k, 0) >= v for k, v in clock1.items())

        # If neither dominates, it's a concurrent modification
        return not (clock1_dominates or clock2_dominates)

    def _determine_conflict_type(
        self, local_pattern: dict[str, Any], server_pattern: dict[str, Any]
    ) -> ConflictType:
        """Determine the type of conflict based on pattern differences."""
        local_content = local_pattern.get("document", "")
        server_content = server_pattern.get("document", "")

        local_meta = local_pattern.get("metadata", {})
        server_meta = server_pattern.get("metadata", {})

        # Check for content conflicts
        if local_content != server_content:
            return ConflictType.CONTENT_CONFLICT

        # Check for metadata/schema conflicts
        if set(local_meta.keys()) != set(server_meta.keys()):
            return ConflictType.SCHEMA_CONFLICT

        # Check for value conflicts in metadata
        for key in local_meta:
            if local_meta[key] != server_meta.get(key):
                return ConflictType.CONCURRENT_EDIT

        return ConflictType.VERSION_MISMATCH

    def resolve_conflict(
        self, conflict: dict[str, Any], strategy: Optional[ResolutionStrategy] = None
    ) -> dict[str, Any]:
        """
        Resolve a conflict using the specified strategy.

        Args:
            conflict: Conflict description from detect_conflict
            strategy: Resolution strategy to use

        Returns:
            Resolution result with resolved pattern
        """
        strategy = strategy or self.default_strategy

        try:
            if strategy == ResolutionStrategy.LOCAL_WINS:
                return self._resolve_local_wins(conflict)
            elif strategy == ResolutionStrategy.SERVER_WINS:
                return self._resolve_server_wins(conflict)
            elif strategy == ResolutionStrategy.NEWEST_WINS:
                return self._resolve_newest_wins(conflict)
            elif strategy == ResolutionStrategy.MERGE:
                return self._resolve_merge(conflict)
            else:  # MANUAL
                return self._resolve_manual(conflict)

        except Exception as e:
            self.logger.error(f"Error resolving conflict: {e}")
            return {"success": False, "error": str(e), "conflict": conflict}

    def _resolve_local_wins(self, conflict: dict[str, Any]) -> dict[str, Any]:
        """Resolve conflict by keeping local version."""
        local_pattern = conflict["local_version"]

        # Update vector clock to indicate resolution
        new_clock = self._merge_vector_clocks(
            conflict["local_clock"], conflict["server_clock"]
        )

        resolved_pattern = {
            **local_pattern,
            "vector_clock": new_clock,
            "resolved_at": datetime.now().isoformat(),
            "resolution_strategy": "local_wins",
        }

        return {
            "success": True,
            "strategy": "local_wins",
            "resolved_pattern": resolved_pattern,
        }

    def _resolve_server_wins(self, conflict: dict[str, Any]) -> dict[str, Any]:
        """Resolve conflict by keeping server version."""
        server_pattern = conflict["server_version"]

        # Update vector clock
        new_clock = self._merge_vector_clocks(
            conflict["local_clock"], conflict["server_clock"]
        )

        resolved_pattern = {
            **server_pattern,
            "vector_clock": new_clock,
            "resolved_at": datetime.now().isoformat(),
            "resolution_strategy": "server_wins",
        }

        return {
            "success": True,
            "strategy": "server_wins",
            "resolved_pattern": resolved_pattern,
        }

    def _resolve_newest_wins(self, conflict: dict[str, Any]) -> dict[str, Any]:
        """Resolve conflict by keeping the newest version."""
        local_pattern = conflict["local_version"]
        server_pattern = conflict["server_version"]

        # Compare timestamps
        local_time = local_pattern.get("updated_at")
        server_time = server_pattern.get("updated_at")

        if not local_time or not server_time:
            # Fall back to local wins if timestamps unavailable
            return self._resolve_local_wins(conflict)

        try:
            local_dt = datetime.fromisoformat(local_time.replace("Z", "+00:00"))
            server_dt = datetime.fromisoformat(server_time.replace("Z", "+00:00"))

            if local_dt >= server_dt:
                return self._resolve_local_wins(conflict)
            else:
                return self._resolve_server_wins(conflict)

        except Exception:
            # Fall back to local wins if timestamp parsing fails
            return self._resolve_local_wins(conflict)

    def _resolve_merge(self, conflict: dict[str, Any]) -> dict[str, Any]:
        """Resolve conflict by merging local and server versions."""
        local_pattern = conflict["local_version"]
        server_pattern = conflict["server_version"]

        try:
            # Merge metadata (server values take precedence for conflicts)
            merged_metadata = {**local_pattern.get("metadata", {})}
            merged_metadata.update(server_pattern.get("metadata", {}))

            # For document content, prefer the longer version
            local_doc = local_pattern.get("document", "")
            server_doc = server_pattern.get("document", "")

            merged_doc = local_doc if len(local_doc) > len(server_doc) else server_doc

            # Create merged pattern
            merged_pattern = {
                "id": local_pattern["id"],
                "document": merged_doc,
                "metadata": merged_metadata,
                "vector_clock": self._merge_vector_clocks(
                    conflict["local_clock"], conflict["server_clock"]
                ),
                "resolved_at": datetime.now().isoformat(),
                "resolution_strategy": "merge",
                "merge_source": "auto_merge",
            }

            # Keep other fields from local version
            for key, value in local_pattern.items():
                if key not in merged_pattern:
                    merged_pattern[key] = value

            return {
                "success": True,
                "strategy": "merge",
                "resolved_pattern": merged_pattern,
            }

        except Exception as e:
            self.logger.error(f"Error in merge resolution: {e}")
            # Fall back to local wins
            return self._resolve_local_wins(conflict)

    def _resolve_manual(self, conflict: dict[str, Any]) -> dict[str, Any]:
        """Return conflict for manual resolution."""
        return {
            "success": False,
            "strategy": "manual",
            "requires_manual_resolution": True,
            "conflict": conflict,
            "resolution_options": ["local_wins", "server_wins", "newest_wins", "merge"],
        }

    def _merge_vector_clocks(
        self, clock1: dict[str, int], clock2: dict[str, int]
    ) -> dict[str, int]:
        """Merge two vector clocks by taking the maximum value for each key."""
        merged = clock1.copy()

        for key, value in clock2.items():
            merged[key] = max(merged.get(key, 0), value)

        return merged

    def suggest_resolution_strategy(
        self, conflict: dict[str, Any]
    ) -> ResolutionStrategy:
        """Suggest the best resolution strategy for a conflict."""
        conflict_type = ConflictType(conflict.get("type", "concurrent_edit"))

        # Strategy suggestions based on conflict type
        if conflict_type == ConflictType.VERSION_MISMATCH:
            return ResolutionStrategy.NEWEST_WINS
        elif conflict_type == ConflictType.SCHEMA_CONFLICT:
            return ResolutionStrategy.MANUAL
        elif conflict_type == ConflictType.CONTENT_CONFLICT:
            # Check if content can be safely merged
            local_doc = conflict["local_version"].get("document", "")
            server_doc = conflict["server_version"].get("document", "")

            if self._can_auto_merge_content(local_doc, server_doc):
                return ResolutionStrategy.MERGE
            else:
                return ResolutionStrategy.MANUAL
        else:
            return ResolutionStrategy.NEWEST_WINS

    def _can_auto_merge_content(self, content1: str, content2: str) -> bool:
        """Check if two content strings can be safely auto-merged."""
        # Simple heuristic: if one is a subset of the other, merge is safe
        if content1 in content2 or content2 in content1:
            return True

        # If contents are similar (>80% similarity), merge might be safe
        similarity = self._calculate_similarity(content1, content2)
        return similarity > 0.8

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        if not text1 or not text2:
            return 0.0

        # Simple Jaccard similarity on words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0
