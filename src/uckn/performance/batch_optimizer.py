"""
UCKN Batch Processing Optimizer

- Efficient batching for embeddings and DB ops
- Bulk insert/update/search
- Memory-efficient chunking
- Progress tracking and cancellation
"""

import logging
import threading
from collections.abc import Callable, Iterator
from typing import Any


class BatchProcessor:
    """
    Batch processor for large-scale operations.
    - Batches items for embedding or DB ops
    - Supports progress tracking and cancellation
    """

    def __init__(self, batch_size=128):
        self.batch_size = batch_size
        self.logger = logging.getLogger(__name__)
        self._cancel_event = threading.Event()

    def batch_iter(self, items: list[Any]) -> Iterator[list[Any]]:
        """Yield items in batches."""
        for i in range(0, len(items), self.batch_size):
            if self._cancel_event.is_set():
                break
            yield items[i : i + self.batch_size]

    def process_batches(
        self,
        items: list[Any],
        process_fn: Callable[[list[Any]], Any],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[Any]:
        """Process items in batches, with optional progress callback."""
        results = []
        total = len(items)
        processed = 0
        for batch in self.batch_iter(items):
            if self._cancel_event.is_set():
                self.logger.info("Batch processing cancelled.")
                break
            res = process_fn(batch)
            results.extend(res if isinstance(res, list) else [res])
            processed += len(batch)
            if progress_callback:
                progress_callback(processed, total)
        return results

    def cancel(self):
        """Cancel ongoing batch processing."""
        self._cancel_event.set()

    def reset(self):
        """Reset cancellation state."""
        self._cancel_event.clear()


BatchProcessor = BatchProcessor
