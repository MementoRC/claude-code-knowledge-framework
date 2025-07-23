"""
Tests for UCKN Synchronization Manager.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.uckn.sync.conflict_resolver import ConflictResolver
from src.uckn.sync.sync_manager import SyncDirection, SyncManager, SyncMode, SyncStatus
from src.uckn.sync.sync_queue import SyncQueue


@pytest.fixture
def mock_local_db():
    """Mock local unified database."""
    db = Mock()
    db.get_pattern.return_value = {
        "id": "test-pattern-1",
        "document": "Test pattern content",
        "metadata": {"type": "test"},
        "vector_clock": {"local": 1}
    }
    return db


@pytest.fixture
def sync_manager(mock_local_db):
    """Create sync manager instance for testing."""
    return SyncManager(
        local_db=mock_local_db,
        server_url="http://test-server.com",
        websocket_url="ws://test-server.com/ws",
        auth_token="test-token"
    )


@pytest.mark.asyncio
async def test_sync_manager_initialization(sync_manager):
    """Test sync manager initialization."""
    assert sync_manager.status == SyncStatus.IDLE
    assert sync_manager.sync_progress == 0.0
    assert not sync_manager.is_online
    assert sync_manager.last_sync_time is None


@pytest.mark.asyncio
async def test_sync_manager_start_stop(sync_manager):
    """Test starting and stopping sync manager."""
    with patch.object(sync_manager, '_connect_websocket', new_callable=AsyncMock):
        await sync_manager.start()

    await sync_manager.stop()


@pytest.mark.asyncio
async def test_sync_full_mode(sync_manager):
    """Test full synchronization mode."""
    with patch.object(sync_manager, '_perform_sync', new_callable=AsyncMock) as mock_sync:
        mock_sync.return_value = {
            "success": True,
            "conflicts": [],
            "stats": {"patterns_uploaded": 5, "patterns_downloaded": 3}
        }

        result = await sync_manager.sync(mode=SyncMode.FULL)

        assert result["success"] is True
        assert sync_manager.status == SyncStatus.COMPLETED
        mock_sync.assert_called_once()


@pytest.mark.asyncio
async def test_sync_with_conflicts(sync_manager):
    """Test synchronization with conflicts."""
    with patch.object(sync_manager, '_perform_sync', new_callable=AsyncMock) as mock_sync:
        mock_sync.return_value = {
            "success": True,
            "conflicts": [{"pattern_id": "test-1", "type": "content_conflict"}],
            "stats": {"patterns_uploaded": 2, "patterns_downloaded": 1}
        }

        result = await sync_manager.sync()

        assert result["success"] is True
        assert len(result["conflicts"]) == 1
        assert sync_manager.status == SyncStatus.CONFLICT


@pytest.mark.asyncio
async def test_sync_failure(sync_manager):
    """Test sync failure handling."""
    with patch.object(sync_manager, '_perform_sync', new_callable=AsyncMock) as mock_sync:
        mock_sync.side_effect = Exception("Network error")

        result = await sync_manager.sync()

        assert "error" in result
        assert sync_manager.status == SyncStatus.FAILED


def test_sync_callbacks(sync_manager):
    """Test sync callback system."""
    callback_called = False
    callback_event = None

    def test_callback(event):
        nonlocal callback_called, callback_event
        callback_called = True
        callback_event = event

    sync_manager.add_sync_callback(test_callback)

    # Trigger callback
    sync_manager._notify_callbacks({"type": "test_event", "data": "test"})

    assert callback_called
    assert callback_event["type"] == "test_event"


def test_get_sync_status(sync_manager):
    """Test sync status reporting."""
    status = sync_manager.get_sync_status()

    assert "status" in status
    assert "progress" in status
    assert "last_sync" in status
    assert "is_online" in status
    assert "queue_size" in status
    assert "vector_clock" in status


@pytest.mark.asyncio
async def test_selective_sync(sync_manager):
    """Test selective synchronization."""
    pattern_ids = ["pattern-1", "pattern-2"]

    with patch.object(sync_manager, '_perform_sync', new_callable=AsyncMock) as mock_sync:
        mock_sync.return_value = {
            "success": True,
            "conflicts": [],
            "stats": {"patterns_uploaded": 2, "patterns_downloaded": 0}
        }

        result = await sync_manager.sync(
            mode=SyncMode.SELECTIVE,
            direction=SyncDirection.UPLOAD,
            pattern_ids=pattern_ids
        )

        assert result["success"] is True
        mock_sync.assert_called_once_with(
            SyncMode.SELECTIVE,
            SyncDirection.UPLOAD,
            pattern_ids
        )
