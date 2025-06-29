"""
UCKN Synchronization Manager
Handles bi-directional sync between local and server knowledge stores.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from ..storage.unified_database import UnifiedDatabase
from .conflict_resolver import ConflictResolver
from .sync_queue import SyncQueue


class SyncMode(Enum):
    """Synchronization modes."""
    FULL = "full"
    INCREMENTAL = "incremental"
    SELECTIVE = "selective"


class SyncDirection(Enum):
    """Synchronization directions."""
    UPLOAD = "upload"
    DOWNLOAD = "download"
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(Enum):
    """Synchronization status."""
    IDLE = "idle"
    SYNCING = "syncing"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"


class SyncManager:
    """
    Manages real-time synchronization between local and server knowledge stores.
    
    Features:
    - Bi-directional sync with conflict resolution
    - Offline mode with sync queue
    - Real-time updates via WebSocket
    - Progress monitoring and status reporting
    """
    
    def __init__(
        self,
        local_db: UnifiedDatabase,
        server_url: str,
        websocket_url: str,
        auth_token: Optional[str] = None
    ):
        self.local_db = local_db
        self.server_url = server_url
        self.websocket_url = websocket_url
        self.auth_token = auth_token
        
        self.logger = logging.getLogger(__name__)
        self.conflict_resolver = ConflictResolver()
        self.sync_queue = SyncQueue()
        
        # Sync state
        self.status = SyncStatus.IDLE
        self.last_sync_time: Optional[datetime] = None
        self.sync_progress = 0.0
        self.is_online = False
        
        # WebSocket connection
        self.websocket = None
        self.sync_callbacks: List[Callable] = []
        
        # Vector clocks for conflict detection
        self.vector_clock: Dict[str, int] = {}
        
    async def start(self):
        """Start the synchronization manager."""
        self.logger.info("Starting sync manager...")
        
        # Initialize WebSocket connection for real-time updates
        await self._connect_websocket()
        
        # Start background sync task
        asyncio.create_task(self._background_sync_loop())
        
    async def stop(self):
        """Stop the synchronization manager."""
        self.logger.info("Stopping sync manager...")
        
        if self.websocket:
            await self.websocket.close()
        
    def add_sync_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add a callback for sync status updates."""
        self.sync_callbacks.append(callback)
        
    def _notify_callbacks(self, event: Dict[str, Any]):
        """Notify all registered callbacks of sync events."""
        for callback in self.sync_callbacks:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Error in sync callback: {e}")
    
    async def sync(
        self,
        mode: SyncMode = SyncMode.INCREMENTAL,
        direction: SyncDirection = SyncDirection.BIDIRECTIONAL,
        pattern_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform synchronization between local and server stores.
        
        Args:
            mode: Synchronization mode (full, incremental, selective)
            direction: Sync direction (upload, download, bidirectional)
            pattern_ids: Specific pattern IDs for selective sync
            
        Returns:
            Sync result with status, conflicts, and statistics
        """
        if self.status == SyncStatus.SYNCING:
            return {"error": "Sync already in progress"}
        
        self.status = SyncStatus.SYNCING
        self.sync_progress = 0.0
        
        try:
            result = await self._perform_sync(mode, direction, pattern_ids)
            self.status = SyncStatus.COMPLETED if not result.get("conflicts") else SyncStatus.CONFLICT
            self.last_sync_time = datetime.now()
            
            # Notify callbacks
            self._notify_callbacks({
                "type": "sync_completed",
                "status": self.status.value,
                "result": result
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Sync failed: {e}")
            self.status = SyncStatus.FAILED
            
            self._notify_callbacks({
                "type": "sync_failed",
                "error": str(e)
            })
            
            return {"error": str(e)}
    
    async def _perform_sync(
        self,
        mode: SyncMode,
        direction: SyncDirection,
        pattern_ids: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Internal sync implementation."""
        conflicts = []
        stats = {
            "patterns_uploaded": 0,
            "patterns_downloaded": 0,
            "conflicts_detected": 0,
            "total_items": 0
        }
        
        try:
            # Get local patterns
            if mode == SyncMode.SELECTIVE and pattern_ids:
                local_patterns = []
                for pid in pattern_ids:
                    pattern = self.local_db.get_pattern(pid)
                    if pattern:
                        local_patterns.append(pattern)
            else:
                local_patterns = self._get_local_patterns_since_last_sync(mode)
            
            stats["total_items"] = len(local_patterns)
            
            # Upload patterns if needed
            if direction in [SyncDirection.UPLOAD, SyncDirection.BIDIRECTIONAL]:
                upload_result = await self._upload_patterns(local_patterns)
                stats["patterns_uploaded"] = upload_result["uploaded"]
                conflicts.extend(upload_result.get("conflicts", []))
            
            # Download patterns if needed  
            if direction in [SyncDirection.DOWNLOAD, SyncDirection.BIDIRECTIONAL]:
                download_result = await self._download_patterns()
                stats["patterns_downloaded"] = download_result["downloaded"]
                conflicts.extend(download_result.get("conflicts", []))
            
            stats["conflicts_detected"] = len(conflicts)
            
            return {
                "success": True,
                "conflicts": conflicts,
                "stats": stats
            }
            
        except Exception as e:
            self.logger.error(f"Error in sync operation: {e}")
            return {"error": str(e)}
    
    def _get_local_patterns_since_last_sync(self, mode: SyncMode) -> List[Dict[str, Any]]:
        """Get local patterns that need syncing."""
        try:
            if mode == SyncMode.FULL or not self.last_sync_time:
                # Get all patterns for full sync
                return self._get_all_local_patterns()
            else:
                # Get patterns modified since last sync
                return self._get_modified_patterns_since(self.last_sync_time)
        except Exception as e:
            self.logger.error(f"Error getting local patterns: {e}")
            return []
    
    def _get_all_local_patterns(self) -> List[Dict[str, Any]]:
        """Get all local patterns."""
        # This would use the unified database to get all patterns
        # For now, return empty list as placeholder
        return []
    
    def _get_modified_patterns_since(self, since: datetime) -> List[Dict[str, Any]]:
        """Get patterns modified since given timestamp."""
        # This would query patterns modified after the timestamp
        # For now, return empty list as placeholder
        return []
    
    async def _upload_patterns(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Upload patterns to server."""
        uploaded = 0
        conflicts = []
        
        for i, pattern in enumerate(patterns):
            try:
                # Check for conflicts using vector clocks
                conflict = await self._check_upload_conflict(pattern)
                if conflict:
                    conflicts.append(conflict)
                    continue
                
                # Upload pattern to server
                success = await self._send_pattern_to_server(pattern)
                if success:
                    uploaded += 1
                    
                # Update progress
                self.sync_progress = (i + 1) / len(patterns) * 0.5  # 50% for upload
                
            except Exception as e:
                self.logger.error(f"Error uploading pattern {pattern.get('id')}: {e}")
        
        return {"uploaded": uploaded, "conflicts": conflicts}
    
    async def _download_patterns(self) -> Dict[str, Any]:
        """Download patterns from server."""
        downloaded = 0
        conflicts = []
        
        try:
            # Get patterns from server that are newer than local
            server_patterns = await self._get_patterns_from_server()
            
            for i, pattern in enumerate(server_patterns):
                try:
                    # Check for conflicts
                    conflict = await self._check_download_conflict(pattern)
                    if conflict:
                        conflicts.append(conflict)
                        continue
                    
                    # Apply pattern to local database
                    success = await self._apply_pattern_locally(pattern)
                    if success:
                        downloaded += 1
                    
                    # Update progress (50% offset for download)
                    self.sync_progress = 0.5 + (i + 1) / len(server_patterns) * 0.5
                    
                except Exception as e:
                    self.logger.error(f"Error downloading pattern {pattern.get('id')}: {e}")
            
        except Exception as e:
            self.logger.error(f"Error downloading patterns: {e}")
        
        return {"downloaded": downloaded, "conflicts": conflicts}
    
    async def _check_upload_conflict(self, pattern: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for conflicts when uploading a pattern."""
        # Get server version of pattern
        server_pattern = await self._get_pattern_from_server(pattern["id"])
        if not server_pattern:
            return None  # No conflict if pattern doesn't exist on server
        
        # Compare vector clocks for conflict detection
        local_clock = pattern.get("vector_clock", {})
        server_clock = server_pattern.get("vector_clock", {})
        
        if self._has_conflict(local_clock, server_clock):
            return {
                "pattern_id": pattern["id"],
                "type": "upload_conflict",
                "local_version": pattern,
                "server_version": server_pattern
            }
        
        return None
    
    async def _check_download_conflict(self, pattern: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for conflicts when downloading a pattern."""
        # Get local version of pattern
        local_pattern = self.local_db.get_pattern(pattern["id"])
        if not local_pattern:
            return None  # No conflict if pattern doesn't exist locally
        
        # Compare vector clocks
        local_clock = local_pattern.get("vector_clock", {})
        server_clock = pattern.get("vector_clock", {})
        
        if self._has_conflict(local_clock, server_clock):
            return {
                "pattern_id": pattern["id"],
                "type": "download_conflict",
                "local_version": local_pattern,
                "server_version": pattern
            }
        
        return None
    
    def _has_conflict(self, clock1: Dict[str, int], clock2: Dict[str, int]) -> bool:
        """Check if two vector clocks indicate a conflict."""
        # Simple conflict detection: if neither clock dominates the other
        clock1_dominates = all(clock1.get(k, 0) >= v for k, v in clock2.items())
        clock2_dominates = all(clock2.get(k, 0) >= v for k, v in clock1.items())
        
        return not (clock1_dominates or clock2_dominates)
    
    async def _send_pattern_to_server(self, pattern: Dict[str, Any]) -> bool:
        """Send a pattern to the server."""
        # Placeholder for actual HTTP request to server
        # In real implementation, this would use httpx or similar
        self.logger.info(f"Uploading pattern {pattern.get('id')} to server")
        await asyncio.sleep(0.1)  # Simulate network delay
        return True
    
    async def _get_patterns_from_server(self) -> List[Dict[str, Any]]:
        """Get patterns from server."""
        # Placeholder for actual HTTP request
        self.logger.info("Downloading patterns from server")
        await asyncio.sleep(0.1)  # Simulate network delay
        return []
    
    async def _get_pattern_from_server(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific pattern from server."""
        # Placeholder for actual HTTP request
        await asyncio.sleep(0.1)  # Simulate network delay
        return None
    
    async def _apply_pattern_locally(self, pattern: Dict[str, Any]) -> bool:
        """Apply a pattern to the local database."""
        try:
            # Extract required fields for local storage
            pattern_id = pattern.get("id")
            document = pattern.get("document", "")
            metadata = pattern.get("metadata", {})
            embedding = pattern.get("embedding", [])
            
            if not pattern_id or not embedding:
                return False
            
            # Add or update pattern in local database
            result = self.local_db.add_pattern(
                document_text=document,
                embedding=embedding,
                metadata=metadata,
                pattern_id=pattern_id
            )
            
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error applying pattern locally: {e}")
            return False
    
    async def _connect_websocket(self):
        """Connect to server WebSocket for real-time updates."""
        try:
            # Placeholder for WebSocket connection
            # In real implementation, this would use websockets library
            self.logger.info(f"Connecting to WebSocket: {self.websocket_url}")
            self.is_online = True
            
            # Start listening for real-time updates
            asyncio.create_task(self._websocket_listener())
            
        except Exception as e:
            self.logger.error(f"Failed to connect WebSocket: {e}")
            self.is_online = False
    
    async def _websocket_listener(self):
        """Listen for real-time updates from server."""
        while self.is_online:
            try:
                # Placeholder for receiving WebSocket messages
                await asyncio.sleep(1)
                
                # When real message received, handle it
                # message = await self.websocket.receive_text()
                # await self._handle_realtime_update(json.loads(message))
                
            except Exception as e:
                self.logger.error(f"WebSocket listener error: {e}")
                break
    
    async def _handle_realtime_update(self, message: Dict[str, Any]):
        """Handle real-time update from server."""
        message_type = message.get("type")
        
        if message_type == "pattern_updated":
            pattern_id = message.get("pattern_id")
            self.logger.info(f"Received real-time update for pattern {pattern_id}")
            
            # Queue the pattern for sync
            self.sync_queue.add_pattern(pattern_id)
            
            # Notify callbacks
            self._notify_callbacks({
                "type": "realtime_update",
                "pattern_id": pattern_id,
                "message": message
            })
    
    async def _background_sync_loop(self):
        """Background task for periodic sync operations."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Process sync queue if online and not currently syncing
                if self.is_online and self.status == SyncStatus.IDLE:
                    if self.sync_queue.has_pending():
                        pattern_ids = self.sync_queue.get_pending_patterns()
                        await self.sync(
                            mode=SyncMode.SELECTIVE,
                            direction=SyncDirection.BIDIRECTIONAL,
                            pattern_ids=pattern_ids
                        )
                        self.sync_queue.clear_processed(pattern_ids)
                
            except Exception as e:
                self.logger.error(f"Background sync loop error: {e}")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status."""
        return {
            "status": self.status.value,
            "progress": self.sync_progress,
            "last_sync": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "is_online": self.is_online,
            "queue_size": self.sync_queue.size(),
            "vector_clock": self.vector_clock.copy()
        }