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


def fetch_all_recent_papers(
    days=14,
    max_per_cat=250,
    ignore_cache=False,
    days_back_start=None,
    days_back_end=None,
):
    """
    Fetches papers from a specific date range across all categories
    and deduplicates them into a global dictionary.

    Args:
        days: Number of days to look back (used if days_back_start/end not provided)
        max_per_cat: Maximum papers per category
        ignore_cache: Whether to ignore cache
        days_back_start: Start of date range (days back from today, e.g., 14 = 14 days ago)
        days_back_end: End of date range (days back from today, e.g., 7 = 7 days ago)
                      If provided, only papers between start and end are fetched
    """
    now = datetime.now(timezone.utc)

    # Determine date range
    if days_back_start is not None and days_back_end is not None:
        # Fetch papers from the week prior (e.g., 14 days ago to 7 days ago)
        # days_back_start=14 means 14 days ago (older), days_back_end=7 means 7 days ago (newer)
        cutoff_date_old = now - timedelta(
            days=days_back_start
        )  # Papers older than this are excluded (14 days ago)
        cutoff_date_new = now - timedelta(
            days=days_back_end
        )  # Papers newer than this are excluded (7 days ago)
        print(
            f"1. FETCHING PAPERS from {cutoff_date_old.date()} to {cutoff_date_new.date()} (week prior: days {days_back_start}-{days_back_end} back)"
        )
    else:
        # Legacy behavior: fetch last N days
        start_date = now - timedelta(days=days)
        print(
            f"1. FETCHING PAPERS from {start_date.date()} to {now.date()} - last {days} days"
        )
        cutoff_date_old = start_date
        cutoff_date_new = None

    if is_cache_valid() and not ignore_cache:
        print("Paper metadata cache found, loading from file!")
        cached_papers = load_papers_from_cache()
        if cached_papers:
            return cached_papers
        print("Cache loading failed, proceeding with API calls!")

    # No valid cache, proceed with normal fetching
    global_papers = {}
    # client = arxiv.Client()
    client = arxiv.Client(
        page_size=2000,
        delay_seconds=10.0,
        num_retries=5,
    )

    for cat_code in FILTER_CATEGORIES.keys():
        print(f"Fetching {cat_code}...")
        search = arxiv.Search(
            query=f"cat:{cat_code}",
            max_results=max_per_cat,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        try:
            papers_in_range = 0
            papers_too_old = 0
            for paper in client.results(search):
                # Skip papers that are too recent (if date range specified)
                if cutoff_date_new is not None and paper.published > cutoff_date_new:
                    continue

                # Stop processing if paper is older than cutoff
                if paper.published < cutoff_date_old:
                    papers_too_old += 1
                    # Continue a bit more to ensure we don't miss papers due to sorting issues
                    if (
                        papers_too_old > 100
                    ):  # Allow 100 papers past cutoff before truly stopping
                        break
                    continue

                clean_id = paper.get_short_id().split("v")[0]

                # Deduplication Logic
                if clean_id not in global_papers:
                    global_papers[clean_id] = paper
                    papers_in_range += 1

            print(f"  {cat_code}: {papers_in_range} papers in date range")
        except Exception as e:
            print(f"Error fetching {cat_code}: {e}")
    print(f"\nTotal unique papers fetched: {len(global_papers)}")

    # Save to cache for future use today
    save_paper_metadata_to_cache(global_papers)

    return global_papers
