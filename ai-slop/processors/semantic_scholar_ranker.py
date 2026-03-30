"""Semantic Scholar ranking processor."""

import json
import os
from datetime import date, datetime
from typing import Any, Dict, List

import requests

from schema import Item, ProcessedItem
from processors.base import DataProcessor


class SemanticScholarRanker(DataProcessor):
    """Rank items using Semantic Scholar citation metrics."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.batch_size = config.get("batch_size", 500)
        self.cache_dir = config.get("cache_dir", "cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    def process(self, items: List[Item]) -> List[ProcessedItem]:
        """Process items by ranking them with Semantic Scholar."""
        # Check cache first
        cache_file = self._get_cache_filename()
        if self._is_cache_valid(cache_file):
            cached_scores = self._load_from_cache(cache_file)
            processed_items = self._apply_scores(items, cached_scores)
        else:
            # Score with API
            scores = self._score_with_semantic_scholar(items)
            processed_items = self._apply_scores(items, scores)
            # Save to cache
            self._save_to_cache(cache_file, scores)

        # Sort by score
        processed_items.sort(key=lambda x: x.score, reverse=True)
        
        # Assign ranks
        for idx, item in enumerate(processed_items, 1):
            item.rank = idx

        return processed_items

    def _score_with_semantic_scholar(self, items: List[Item]) -> Dict[str, float]:
        """Score items using Semantic Scholar API."""
        scores = {}
        arxiv_ids = [item.source_id for item in items if item.source_type == "arxiv"]

        if not arxiv_ids:
            return scores

        s2_url = "https://api.semanticscholar.org/graph/v1/paper/batch"
        params = {
            "fields": "externalIds,title,citationCount,influentialCitationCount,referenceCount"
        }

        # Process in batches
        for i in range(0, len(arxiv_ids), self.batch_size):
            batch_ids = arxiv_ids[i : i + self.batch_size]
            s2_request_ids = [f"ARXIV:{aid}" for aid in batch_ids]

            try:
                response = requests.post(
                    s2_url, params=params, json={"ids": s2_request_ids}, timeout=15
                )
                response.raise_for_status()
                s2_data = response.json()

                for item in s2_data:
                    if (
                        item is not None
                        and "externalIds" in item
                        and "ArXiv" in item["externalIds"]
                    ):
                        aid = item["externalIds"]["ArXiv"]
                        citations = item.get("citationCount") or 0
                        influential = item.get("influentialCitationCount") or 0
                        references = item.get("referenceCount") or 0

                        # Quality Score Formula
                        score = (influential * 3) + citations + (references * 0.01)
                        scores[aid] = score

            except Exception as e:
                print(f"Error scoring batch: {e}")

        # Assign 0 to unscored items
        for aid in arxiv_ids:
            if aid not in scores:
                scores[aid] = 0.0

        return scores

    def _apply_scores(
        self, items: List[Item], scores: Dict[str, float]
    ) -> List[ProcessedItem]:
        """Apply scores to items."""
        processed_items = []
        for item in items:
            score = scores.get(item.source_id, 0.0)
            processed_item = ProcessedItem(
                item=item,
                score=score,
                processing_metadata={"scorer": "semantic_scholar"},
            )
            processed_items.append(processed_item)
        return processed_items

    def _get_cache_filename(self) -> str:
        """Generate cache filename based on today's date."""
        today = date.today().strftime("%Y-%m-%d")
        return os.path.join(self.cache_dir, f"arxiv_ranking_{today}.json")

    def _is_cache_valid(self, cache_file: str) -> bool:
        """Check if cache exists and is from today."""
        if not os.path.exists(cache_file):
            return False
        file_mtime = datetime.fromtimestamp(os.path.getmtime(cache_file)).date()
        return file_mtime == date.today()

    def _save_to_cache(self, cache_file: str, scores: Dict[str, float]) -> None:
        """Save scores to cache file."""
        try:
            with open(cache_file, "w") as f:
                json.dump(scores, f, indent=2)
        except Exception as e:
            print(f"Error saving ranking to cache: {e}")

    def _load_from_cache(self, cache_file: str) -> Dict[str, float]:
        """Load scores from cache file."""
        try:
            with open(cache_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading ranking from cache: {e}")
            return {}
