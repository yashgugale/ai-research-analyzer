import json
import os
from datetime import date, datetime, timedelta, timezone

import arxiv
import requests
from config import CACHE_DIR, CATEGORIES, OUTPUT_DIR
from slugify import slugify

# On average there are about 150-250 papers per day & we want to look back two weeks
MAX_PER_DAY = 250
MAX_DAYS = 14
MAX_PER_CAT = MAX_PER_DAY * MAX_DAYS


def get_cache_filename():
    """Generate cache filename based on today's date."""
    today = date.today().strftime("%Y-%m-%d")
    return os.path.join(CACHE_DIR, f"papers_{today}.json")


def is_cache_valid():
    """Check if cache exists and is from today."""
    cache_file = get_cache_filename()
    if not os.path.exists(cache_file):
        return False

    # Check if file was created today
    file_mtime = datetime.fromtimestamp(os.path.getmtime(cache_file)).date()
    return file_mtime == date.today()


def save_papers_to_cache(papers):
    """Save papers to cache file using JSON."""
    cache_file = get_cache_filename()
    try:
        serializable_papers = {}
        for paper_id, data in papers.items():
            paper = data["paper"]
            serializable_papers[paper_id] = {
                "paper": {
                    "title": paper.title,
                    "authors": [author.name for author in paper.authors],
                    "summary": paper.summary,
                    "published": paper.published.isoformat(),
                    "entry_id": paper.entry_id,
                    "primary_category": paper.primary_category,
                    "categories": paper.categories,
                },
                "categories": data["categories"],
                "score": data.get("score", 0),
            }
        with open(cache_file, "w") as f:
            json.dump(serializable_papers, f, indent=2)
        print(f"Saved {len(papers)} papers to cache: {cache_file}")
    except Exception as e:
        print(f"Error saving to cache: {e}")


def load_papers_from_cache():
    """Load papers from cache file."""
    cache_file = get_cache_filename()
    try:
        with open(cache_file, "r") as f:
            papers = json.load(f)
        print(f"Loaded {len(papers)} papers from cache: {cache_file}")
        return papers
    except Exception as e:
        print(f"Error loading from cache: {e}")
        return None


def fetch_all_recent_papers(days=14, max_per_cat=MAX_PER_CAT):
    """
    Fetches all papers from the last 14 days across all categories
    and deduplicates them into a global dictionary.
    """
    print(f"--- FETCHING PAPERS (LAST {days} DAYS) ---")

    # Check if we have valid cache from today
    if is_cache_valid():
        print("Found valid cache from today, loading from file...")
        cached_papers = load_papers_from_cache()
        if cached_papers:
            return cached_papers
        print("Cache loading failed, proceeding with API calls...")

    # No valid cache, proceed with normal fetching
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    global_papers = {}
    client = arxiv.Client()

    for cat_code in CATEGORIES.keys():
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
                    global_papers[clean_id] = {
                        "paper": paper,
                        "categories": [
                            cat_code
                        ],  # Track which categories it belongs to
                    }
                else:
                    # If already seen, just add the cross-listed category tag
                    global_papers[clean_id]["categories"].append(cat_code)

        except Exception as e:
            print(f"Error fetching {cat_code}: {e}")

    print(f"\nTotal unique papers fetched: {len(global_papers)}")

    # Save to cache for future use today
    save_papers_to_cache(global_papers)

    return global_papers


def get_ranking_cache_filename():
    """Generate ranking cache filename based on today's date."""
    today = date.today().strftime("%Y-%m-%d")
    return os.path.join(CACHE_DIR, f"ranking_{today}.json")


def is_ranking_cache_valid():
    """Check if ranking cache exists and is from today."""
    cache_file = get_ranking_cache_filename()
    if not os.path.exists(cache_file):
        return False

    # Check if file was created today
    file_mtime = datetime.fromtimestamp(os.path.getmtime(cache_file)).date()
    return file_mtime == date.today()


def save_ranking_to_cache(ranked_list):
    """Save ranked papers to cache file using JSON."""
    cache_file = get_ranking_cache_filename()
    try:
        serializable_ranking = []
        for item in ranked_list:
            paper = item["paper"]
            serializable_item = {
                "paper": {
                    "title": paper.title,
                    "authors": [author.name for author in paper.authors],
                    "summary": paper.summary,
                    "published": paper.published.isoformat(),
                    "entry_id": paper.entry_id,
                    "primary_category": paper.primary_category,
                    "categories": paper.categories,
                },
                "categories": item["categories"],
                "score": item.get("score", 0),
            }
            serializable_ranking.append(serializable_item)
        with open(cache_file, "w") as f:
            json.dump(serializable_ranking, f, indent=2)
        print(f"Saved {len(ranked_list)} ranked papers to cache: {cache_file}")
    except Exception as e:
        print(f"Error saving ranking to cache: {e}")


def load_ranking_from_cache():
    """Load ranked papers from cache file."""
    cache_file = get_ranking_cache_filename()
    try:
        with open(cache_file, "r") as f:
            ranked_list = json.load(f)
        print(f"Loaded {len(ranked_list)} ranked papers from cache: {cache_file}")
        return ranked_list
    except Exception as e:
        print(f"Error loading ranking from cache: {e}")
        return None


def score_and_rank_papers(global_papers):
    """
    Sends all deduplicated papers to Semantic Scholar in batches,
    calculates the Quality Score, and returns a globally ranked list.
    """
    print("\n--- SCORING & RANKING (SEMANTIC SCHOLAR) ---")

    # Check if we have valid ranking cache from today
    if is_ranking_cache_valid():
        print("Found valid ranking cache from today, loading from file...")
        cached_ranking = load_ranking_from_cache()
        if cached_ranking:
            return cached_ranking
        print("Ranking cache loading failed, proceeding with API calls...")

    # No valid cache, proceed with normal scoring
    s2_url = "https://api.semanticscholar.org/graph/v1/paper/batch"
    params = {
        "fields": "externalIds,title,citationCount,influentialCitationCount,referenceCount"
    }

    arxiv_ids = list(global_papers.keys())

    # Semantic Scholar allows a maximum of 500 IDs per batch request
    batch_size = 500
    for i in range(0, len(arxiv_ids), batch_size):
        batch_ids = arxiv_ids[i : i + batch_size]
        s2_request_ids = [f"ARXIV:{aid}" for aid in batch_ids]

        print(f"Evaluating batch {i // batch_size + 1}...")
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

                    if aid in global_papers:
                        global_papers[aid]["score"] = score

        except Exception as e:
            print(f"Error scoring batch {i // batch_size + 1}: {e}")

    # Assign a score of 0 to any papers that didn't receive one (too new, API error, etc.)
    for aid, data in global_papers.items():
        if "score" not in data:
            data["score"] = 0

    # Convert the dictionary to a list and sort globally by score (highest to lowest)
    ranked_list = list(global_papers.values())
    ranked_list.sort(key=lambda x: x["score"], reverse=True)

    # Save to cache for future use today
    save_ranking_to_cache(ranked_list)

    return ranked_list


def download_paper(paper, category_code):
    """Helper function to format folders and download the PDF."""
    # Handle both arxiv objects and cached dictionaries
    if isinstance(paper, dict):
        # Cached paper (dictionary)
        clean_id = paper["entry_id"].split("/abs/")[-1].split("v")[0]
        title = paper["title"]
        entry_id = paper["entry_id"]
        is_cached = True
    else:
        # Fresh arxiv object
        clean_id = paper.get_short_id().split("v")[0]
        title = paper.title
        entry_id = paper.entry_id
        is_cached = False

    folder_name = slugify(f"{category_code}-{clean_id}-{title}")
    folder_path = os.path.join(OUTPUT_DIR, folder_name)

    os.makedirs(folder_path, exist_ok=True)

    pdf_path = os.path.join(folder_path, "paper.pdf")
    if not os.path.exists(pdf_path):
        if not is_cached:
            paper.download_pdf(dirpath=folder_path, filename="paper.pdf")
            print(f"  -> Downloaded PDF to: {folder_path}")
        else:
            print(f"  -> PDF not available (cached paper): {folder_path}")
    else:
        print(f"  -> PDF already exists in: {folder_path}")

    return {
        "title": title,
        "domain": CATEGORIES[category_code],
        "folder_path": folder_path,
        "pdf_path": pdf_path,
        "arxiv_url": entry_id,
        "arxiv_id": clean_id,
    }
