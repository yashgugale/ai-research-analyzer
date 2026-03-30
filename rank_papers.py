import json
import os
import time
from datetime import date

import requests
from config import CACHE_DIR

PAPER_RANK_FOLDER_NAME = "paper_ranked"


def get_cached_file(folder_name=None, file_name=None):
    """Generate cache filename based on today's date."""
    folder_path = os.path.join(CACHE_DIR, folder_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return os.path.join(folder_path, file_name)


def is_cache_valid():
    """Check if cache exists and is from today."""
    cache_file = get_cached_file(
        folder_name=PAPER_RANK_FOLDER_NAME,
        file_name=f"{date.today().strftime('%Y-%m-%d')}.json",
    )
    if not os.path.exists(cache_file):
        return False

    return True


def save_ranking_to_cache(ranked_list):
    """Save ranked papers to cache file using JSON."""
    cache_file = get_cached_file(
        folder_name=PAPER_RANK_FOLDER_NAME,
        file_name=f"{date.today().strftime('%Y-%m-%d')}.json",
    )
    try:
        # ranked_list is already a list of dicts with scores
        with open(cache_file, "w") as f:
            json.dump(ranked_list, f, indent=2)
        print(f"Saved {len(ranked_list)} ranked papers to cache: {cache_file}")
    except Exception as e:
        print(f"Error saving ranking to cache: {e}")


def load_ranking_from_cache():
    """Load ranked papers from cache file."""
    cache_file = get_cached_file(
        folder_name=PAPER_RANK_FOLDER_NAME,
        file_name=f"{date.today().strftime('%Y-%m-%d')}.json",
    )
    try:
        with open(cache_file, "r") as f:
            ranked_list = json.load(f)
        print(f"Loaded {len(ranked_list)} ranked papers from cache: {cache_file}")
        return ranked_list
    except Exception as e:
        print(f"Error loading ranking from cache: {e}")
        return None


def score_and_rank_papers(global_papers, ignore_cache=False):
    """
    Sends all deduplicated papers to Semantic Scholar in batches,
    calculates the Quality Score, and returns a globally ranked list.
    """
    print("\n2. SCORING & RANKING papers based on Semantic Scholar data")

    # Check if we have valid ranking cache from today
    if is_cache_valid() and not ignore_cache:
        print("Found valid ranking cache from today, loading from file!")
        cached_ranking = load_ranking_from_cache()
        if cached_ranking:
            return cached_ranking
        print("Ranking cache loading failed, proceeding with API calls!")

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

        # Rate limiting: wait 5 seconds between batches to avoid 429 errors
        if i + batch_size < len(arxiv_ids):
            print("Waiting 5 seconds before next batch...")
            time.sleep(5)

    # Convert the dictionary to a list and sort globally by score (highest to lowest)
    ranked_list = list(global_papers.values())
    ranked_list.sort(key=lambda x: x["score"], reverse=True)

    # Save to cache for future use today
    save_ranking_to_cache(ranked_list)

    return ranked_list
