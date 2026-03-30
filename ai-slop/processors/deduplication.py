"""Deduplication processor for removing duplicate items."""

from typing import Any, Dict, List

from schema import ProcessedItem

from processors.base import DataProcessor


class DeduplicationProcessor(DataProcessor):
    """Remove duplicate items based on source ID."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.keep_first = config.get("keep_first", True)

    def process(self, items: List[ProcessedItem]) -> List[ProcessedItem]:
        """Remove duplicate items."""
        seen = set()
        deduplicated = []

        for item in items:
            source_id = item.item.source_id
            if source_id not in seen:
                seen.add(source_id)
                deduplicated.append(item)

        return deduplicated
