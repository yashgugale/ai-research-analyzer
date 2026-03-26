import json
import os
from datetime import date, datetime, timedelta, timezone

import arxiv
from config import CACHE_DIR, FILTER_CATEGORIES

PAPER_METADATA_FOLDER_NAME = "paper_metadata"


def get_cached_file(folder_name=None, file_name=None):
    """Generate cache filename based on today's date."""
    folder_path = os.path.join(CACHE_DIR, folder_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return os.path.join(folder_path, file_name)


def is_cache_valid():
    """Check if cache exists and is from today."""
    cache_file = get_cached_file(
        folder_name=PAPER_METADATA_FOLDER_NAME,
        file_name=f"{date.today().strftime('%Y-%m-%d')}.json",
    )
    if not os.path.exists(cache_file):
        return False

    return True


def save_paper_metadata_to_cache(papers):
    """Save papers to cache file using JSON."""
    cache_file = get_cached_file(
        folder_name=PAPER_METADATA_FOLDER_NAME,
        file_name=f"{date.today().strftime('%Y-%m-%d')}.json",
    )
    try:
        serializable_papers = {}
        for paper_id, paper in papers.items():
            serializable_papers[paper_id] = {
                "entry_id": paper.entry_id,
                "title": paper.title,
                "authors": [author.name for author in paper.authors],
                "summary": paper.summary,
                "published": paper.published.isoformat(),
                "primary_category": paper.primary_category,
                "categories": paper.categories,
                "pdf_url": paper.pdf_url,
                "score": 0,
            }
        with open(cache_file, "w") as f:
            json.dump(serializable_papers, f, indent=2)
        print(f"Saved {len(papers)} papers to cache: {cache_file}")
    except Exception as e:
        print(f"Error saving to cache: {e}")


def load_papers_from_cache():
    """Load papers from cache file."""
    cache_file = get_cached_file(
        folder_name=PAPER_METADATA_FOLDER_NAME,
        file_name=f"{date.today().strftime('%Y-%m-%d')}.json",
    )
    try:
        with open(cache_file, "r") as f:
            papers = json.load(f)
        print(f"Loaded {len(papers)} papers from cache: {cache_file}")
        return papers
    except Exception as e:
        print(f"Error loading from cache: {e}")
        return None


def fetch_all_recent_papers(days=14, max_per_cat=250, ignore_cache=False):
    """
    Fetches all papers from the last 14 days across all categories
    and deduplicates them into a global dictionary.
    """
    print(
        f"1. FETCHING PAPERS from {(datetime.now(timezone.utc) - timedelta(days=days)).date()} to {datetime.now(timezone.utc).date()} - last {days} days"
    )

    if is_cache_valid() and not ignore_cache:
        print("Paper metadata cache found, loading from file!")
        cached_papers = load_papers_from_cache()
        if cached_papers:
            return cached_papers
        print("Cache loading failed, proceeding with API calls!")

    # No valid cache, proceed with normal fetching
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    global_papers = {}
    client = arxiv.Client()

    for cat_code in FILTER_CATEGORIES.keys():
        print(f"Fetching {cat_code}...")
        search = arxiv.Search(
            query=f"cat:{cat_code}",
            max_results=max_per_cat,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        try:
            for paper in client.results(search):
                # Stop processing this category if we hit papers older than 14 days
                if paper.published < cutoff_date:
                    break

                clean_id = paper.get_short_id().split("v")[0]

                # Deduplication Logic
                if clean_id not in global_papers:
                    global_papers[clean_id] = paper
        except Exception as e:
            print(f"Error fetching {cat_code}: {e}")
    print(f"\nTotal unique papers fetched: {len(global_papers)}")

    # Save to cache for future use today
    save_paper_metadata_to_cache(global_papers)

    return global_papers
