"""Filter processor for selecting top items."""

from typing import Any, Dict, List

from schema import ProcessedItem
from processors.base import DataProcessor


class FilterProcessor(DataProcessor):
    """Filter and select top N items."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.top_n = config.get("top_n", 14)
        self.min_score = config.get("min_score", 0.0)

    def process(self, items: List[ProcessedItem]) -> List[ProcessedItem]:
        """Filter items by score and select top N."""
        # Filter by minimum score
        filtered = [item for item in items if item.score >= self.min_score]
        
        # Sort by score (descending)
        filtered.sort(key=lambda x: x.score, reverse=True)
        
        # Select top N
        return filtered[: self.top_n]
