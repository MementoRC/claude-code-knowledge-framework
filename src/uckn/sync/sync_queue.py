"""
UCKN Synchronization Queue
Manages offline sync queue for handling updates when server is unavailable.
"""

import json
import logging
from collections import deque
from datetime import datetime
from enum import Enum
from typing import Any


class QueueOperation(Enum):
    """Types of queued operations."""

    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
    SYNC = "sync"


class QueuePriority(Enum):
    """Queue operation priorities."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class SyncQueue:
    """
    Manages a queue of synchronization operations for offline mode.

    Features:
    - Priority-based queuing
    - Duplicate detection and merging
    - Batch processing
    - Persistence across restarts
    """

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.logger = logging.getLogger(__name__)

        # Priority queues for different operation types
        self.queues: dict[QueuePriority, deque[Any]] = {
            priority: deque() for priority in QueuePriority
        }

        # Track patterns that are already queued to avoid duplicates
        self.queued_patterns: set[str] = set()

        # Statistics
        self.stats = {
            "total_queued": 0,
            "total_processed": 0,
            "total_failed": 0,
            "current_size": 0,
        }

    def add_pattern(
        self,
        pattern_id: str,
        operation: QueueOperation = QueueOperation.SYNC,
        priority: QueuePriority = QueuePriority.NORMAL,
        data: dict[str, Any] | None = None,
    ) -> bool:
        """
        Add a pattern operation to the sync queue.

        Args:
            pattern_id: ID of the pattern to sync
            operation: Type of operation to perform
            priority: Priority level for the operation
            data: Additional data for the operation

        Returns:
            True if added successfully, False if queue is full or duplicate
        """
        if self.size() >= self.max_size:
            self.logger.warning(f"Sync queue is full (size: {self.size()})")
            return False

        # Check for duplicates
        if pattern_id in self.queued_patterns:
            self.logger.debug(f"Pattern {pattern_id} already queued, skipping")
            return False

        # Create queue item
        queue_item = {
            "pattern_id": pattern_id,
            "operation": operation.value,
            "priority": priority.value,
            "data": data or {},
            "queued_at": datetime.now().isoformat(),
            "retry_count": 0,
            "last_error": None,
        }

        # Add to appropriate priority queue
        self.queues[priority].append(queue_item)
        self.queued_patterns.add(pattern_id)

        # Update statistics
        self.stats["total_queued"] += 1
        self.stats["current_size"] = self.size()

        self.logger.debug(
            f"Added pattern {pattern_id} to {priority.name} queue "
            f"(operation: {operation.value})"
        )

        return True

    def get_next_batch(self, batch_size: int = 10) -> list[dict[str, Any]]:
        """
        Get the next batch of items to process, ordered by priority.

        Args:
            batch_size: Maximum number of items to return

        Returns:
            List of queue items to process
        """
        batch: list[Any] = []

        # Process queues in priority order (highest first)
        for priority in sorted(QueuePriority, key=lambda p: p.value, reverse=True):
            queue = self.queues[priority]

            while queue and len(batch) < batch_size:
                batch.append(queue.popleft())

        return batch

    def get_pending_patterns(self, limit: int = 100) -> list[str]:
        """
        Get list of pattern IDs that are pending sync.

        Args:
            limit: Maximum number of pattern IDs to return

        Returns:
            List of pattern IDs pending sync
        """
        pattern_ids: list[str] = []

        # Collect from all queues
        for priority in QueuePriority:
            queue = self.queues[priority]
            for item in list(queue)[: limit - len(pattern_ids)]:
                pattern_ids.append(item["pattern_id"])
                if len(pattern_ids) >= limit:
                    break

            if len(pattern_ids) >= limit:
                break

        return pattern_ids

    def mark_processed(self, pattern_ids: list[str]) -> None:
        """Mark patterns as successfully processed and remove from queue."""
        for pattern_id in pattern_ids:
            if pattern_id in self.queued_patterns:
                self.queued_patterns.remove(pattern_id)
                self.stats["total_processed"] += 1

        self.stats["current_size"] = self.size()

        self.logger.debug(f"Marked {len(pattern_ids)} patterns as processed")

    def mark_failed(self, pattern_id: str, error: str, max_retries: int = 3) -> bool:
        """
        Mark a pattern operation as failed and handle retry logic.

        Args:
            pattern_id: Pattern ID that failed
            error: Error message
            max_retries: Maximum retry attempts

        Returns:
            True if item will be retried, False if permanently failed
        """
        # Find the item in queues
        for priority in QueuePriority:
            queue = self.queues[priority]
            for _i, item in enumerate(queue):
                if item["pattern_id"] == pattern_id:
                    item["retry_count"] += 1
                    item["last_error"] = error

                    if item["retry_count"] >= max_retries:
                        # Remove permanently failed item
                        queue.remove(item)
                        self.queued_patterns.remove(pattern_id)
                        self.stats["total_failed"] += 1
                        self.stats["current_size"] = self.size()

                        self.logger.warning(
                            f"Pattern {pattern_id} permanently failed after "
                            f"{max_retries} retries: {error}"
                        )
                        return False
                    else:
                        self.logger.debug(
                            f"Pattern {pattern_id} failed, retry {item['retry_count']}/{max_retries}: {error}"
                        )
                        return True

        return False

    def clear_processed(self, pattern_ids: list[str]) -> None:
        """Clear processed patterns from the queue."""
        self.mark_processed(pattern_ids)

    def size(self) -> int:
        """Get total number of items in all queues."""
        return sum(len(queue) for queue in self.queues.values())

    def has_pending(self) -> bool:
        """Check if there are any pending items in the queue."""
        return self.size() > 0

    def clear(self) -> None:
        """Clear all items from the queue."""
        for queue in self.queues.values():
            queue.clear()

        self.queued_patterns.clear()
        self.stats["current_size"] = 0

        self.logger.info("Sync queue cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get queue statistics."""
        priority_counts = {
            priority.name.lower(): len(self.queues[priority])
            for priority in QueuePriority
        }

        return {
            **self.stats,
            "priority_breakdown": priority_counts,
            "queue_utilization": (
                self.size() / self.max_size if self.max_size > 0 else 0
            ),
        }

    def get_failed_items(self) -> list[dict[str, Any]]:
        """Get items that have failed at least once."""
        failed_items = []

        for queue in self.queues.values():
            for item in queue:
                if item.get("retry_count", 0) > 0:
                    failed_items.append(item)

        return failed_items

    def retry_failed(self, pattern_id: str | None = None) -> int:
        """
        Retry failed items by resetting their retry count.

        Args:
            pattern_id: Specific pattern to retry, or None to retry all

        Returns:
            Number of items reset for retry
        """
        retry_count = 0

        for queue in self.queues.values():
            for item in queue:
                if item.get("retry_count", 0) > 0:
                    if pattern_id is None or item["pattern_id"] == pattern_id:
                        item["retry_count"] = 0
                        item["last_error"] = None
                        retry_count += 1

        self.logger.info(f"Reset {retry_count} failed items for retry")
        return retry_count

    def to_dict(self) -> dict[str, Any]:
        """Serialize queue to dictionary for persistence."""
        queue_data = {}

        for priority, queue in self.queues.items():
            queue_data[priority.name] = list(queue)

        return {
            "queues": queue_data,
            "queued_patterns": list(self.queued_patterns),
            "stats": self.stats,
            "max_size": self.max_size,
        }

    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore queue from serialized dictionary."""
        try:
            # Restore queues
            for priority_name, items in data.get("queues", {}).items():
                try:
                    priority = QueuePriority[priority_name]
                    self.queues[priority] = deque(items)
                except KeyError:
                    self.logger.warning(f"Unknown priority level: {priority_name}")

            # Restore queued patterns set
            self.queued_patterns = set(data.get("queued_patterns", []))

            # Restore stats
            self.stats.update(data.get("stats", {}))

            # Update current size
            self.stats["current_size"] = self.size()

            self.logger.info(f"Restored sync queue with {self.size()} items")

        except Exception as e:
            self.logger.error(f"Error restoring queue from data: {e}")

    def save_to_file(self, file_path: str) -> bool:
        """Save queue to file for persistence."""
        try:
            with open(file_path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)

            self.logger.debug(f"Saved sync queue to {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving queue to file: {e}")
            return False

    def load_from_file(self, file_path: str) -> bool:
        """Load queue from file."""
        try:
            with open(file_path) as f:
                data = json.load(f)

            self.from_dict(data)
            self.logger.debug(f"Loaded sync queue from {file_path}")
            return True

        except FileNotFoundError:
            self.logger.debug(f"Queue file not found: {file_path}")
            return False
        except Exception as e:
            self.logger.error(f"Error loading queue from file: {e}")
            return False
