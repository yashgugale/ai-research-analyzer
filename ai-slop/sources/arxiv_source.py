"""ArXiv data source implementation."""

import json
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List

import arxiv
from schema import Item

from sources.base import DataSource


class ArxivSource(DataSource):
    """Fetch papers from ArXiv."""

    MAX_PER_DAY = 250
    MAX_DAYS = 14

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.categories = config.get("categories", ["cs.LG", "cs.CV", "cs.CL"])
        self.days = config.get("days", 14)
        self.max_per_day = config.get("max_per_day", self.MAX_PER_DAY)
        self.max_per_cat = self.max_per_day * self.days
        self.cache_dir = config.get("cache_dir", "cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    def fetch(self) -> List[Dict[str, Any]]:
        """Fetch papers from ArXiv."""
        # Check cache first
        cache_file = self._get_cache_filename()
        if self._is_cache_valid(cache_file):
            return self._load_from_cache(cache_file)

        # Fetch from API
        papers = self._fetch_from_api()

        # Save to cache
        self._save_to_cache(cache_file, papers)

        return papers

    def parse(self, raw_item: Dict[str, Any]) -> Item:
        """Parse ArXiv paper into Item schema."""
        paper = raw_item["paper"]

        return Item(
            source_type="arxiv",
            source_id=paper.get_short_id().split("v")[0],
            title=paper.title,
            content=paper.summary,
            metadata={
                "authors": [author.name for author in paper.authors],
                "published": paper.published.isoformat(),
                "entry_id": paper.entry_id,
                "primary_category": paper.primary_category,
                "categories": paper.categories,
            },
        )

    def cache_key(self, raw_item: Dict[str, Any]) -> str:
        """Generate cache key for ArXiv paper."""
        paper = raw_item["paper"]
        return paper.get_short_id().split("v")[0]

    def _fetch_from_api(self) -> List[Dict[str, Any]]:
        """Fetch papers from ArXiv API."""
        papers = {}
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.days)
        client = arxiv.Client()

        for cat_code in self.categories:
            search = arxiv.Search(
                query=f"cat:{cat_code}",
                max_results=self.max_per_cat,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending,
            )

            try:
                for paper in client.results(search):
                    if paper.published < cutoff_date:
                        break

                    clean_id = paper.get_short_id().split("v")[0]
                    if clean_id not in papers:
                        papers[clean_id] = {
                            "paper": paper,
                            "categories": [cat_code],
                        }
                    else:
                        papers[clean_id]["categories"].append(cat_code)

            except Exception as e:
                print(f"Error fetching {cat_code}: {e}")

        return list(papers.values())

    def _get_cache_filename(self) -> str:
        """Generate cache filename based on today's date."""
        today = date.today().strftime("%Y-%m-%d")
        return os.path.join(self.cache_dir, f"arxiv_papers_{today}.json")

    def _is_cache_valid(self, cache_file: str) -> bool:
        """Check if cache exists and is from today."""
        if not os.path.exists(cache_file):
            return False
        file_mtime = datetime.fromtimestamp(os.path.getmtime(cache_file)).date()
        return file_mtime == date.today()

    def _save_to_cache(self, cache_file: str, papers: List[Dict[str, Any]]) -> None:
        """Save papers to cache file."""
        try:
            serializable_papers = {}
            for paper_data in papers:
                paper = paper_data["paper"]
                clean_id = paper.get_short_id().split("v")[0]
                serializable_papers[clean_id] = {
                    "paper": {
                        "title": paper.title,
                        "authors": [author.name for author in paper.authors],
                        "summary": paper.summary,
                        "published": paper.published.isoformat(),
                        "entry_id": paper.entry_id,
                        "primary_category": paper.primary_category,
                        "categories": paper.categories,
                    },
                    "categories": paper_data["categories"],
                }

            with open(cache_file, "w") as f:
                json.dump(serializable_papers, f, indent=2)
        except Exception as e:
            print(f"Error saving to cache: {e}")

    def _load_from_cache(self, cache_file: str) -> List[Dict[str, Any]]:
        """Load papers from cache file."""
        try:
            with open(cache_file, "r") as f:
                papers_dict = json.load(f)
            return list(papers_dict.values())
        except Exception as e:
            print(f"Error loading from cache: {e}")
            return []
