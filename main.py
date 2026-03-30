import os
from datetime import date, datetime, timedelta, timezone

from analysis import analyze_papers
from config import MODEL_PROVIDER, MODEL_PROVIDER_CONFIG, OUTPUT_DIR
from fetch_arxiv_papers import (
    fetch_all_recent_papers,
)
from proofreader import proofread_all_papers
from publish_to_substack import post_all_papers
from rank_papers import score_and_rank_papers

# On average there are about 150-250 papers per day & we want to look at papers from the week prior (7 days back)
# This allows papers to accumulate citations and be more meaningful
MAX_PER_DAY = 250
DAYS_BACK_START = 14  # Start from 14 days ago
DAYS_BACK_END = 7  # End at 7 days ago (the week prior)
MAX_DAYS = DAYS_BACK_END  # Use 7 days for the calculation
MAX_PER_CAT = MAX_PER_DAY * DAYS_BACK_START  # 3500 papers per category


def filter_papers(papers, count):
    print(f"\n3. Filtering {len(papers)} papers to top {count}")
    return papers[:count]


def main():
    print("AI Daily Bytes processor\n")

    # 1. Fetch papers from the week prior (7 days back) to allow for citation accumulation
    global_papers = fetch_all_recent_papers(
        max_per_cat=MAX_PER_CAT,
        ignore_cache=False,
        days_back_start=DAYS_BACK_START,
        days_back_end=DAYS_BACK_END,
    )
    # 2. Score and Rank them globally
    ranked_papers = score_and_rank_papers(global_papers, ignore_cache=False)
    # 3. Select top 14 papers from global ranking and summarize
    top_papers = filter_papers(ranked_papers, 14)

    # 4. Run analysis on top papers
    analyze_papers(top_papers, force_regenerate=False)

    # 5. Proofread all generated markdown files
    papers_date_folder = os.path.join(OUTPUT_DIR, date.today().strftime("%Y-%m-%d"))
    provider_config = MODEL_PROVIDER_CONFIG.get(MODEL_PROVIDER, {})
    proofread_all_papers(
        papers_date_folder, provider_type=MODEL_PROVIDER, **provider_config
    )
    return
    # 6. Publish to Substack
    papers_date_folder = os.path.join(OUTPUT_DIR, date.today().strftime("%Y-%m-%d"))
    # papers_date_folder = os.path.join(OUTPUT_DIR, "2026-03-26")

    # Calculate next day at 10am EST
    now_est = datetime.now(timezone.utc).astimezone()
    tomorrow_10am_est = (now_est + timedelta(days=1)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )
    schedule_start_time = tomorrow_10am_est.isoformat()

    post_all_papers(
        papers_date_folder,
        schedule_start_time=schedule_start_time,
        hours_between_posts=24,
    )


if __name__ == "__main__":
    main()
