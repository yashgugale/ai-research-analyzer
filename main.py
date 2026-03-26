import os
from datetime import date

from analysis import analyze_papers
from config import MODEL_PROVIDER, MODEL_PROVIDER_CONFIG, OUTPUT_DIR
from fetch_arxiv_papers import (
    fetch_all_recent_papers,
)

# from proofreader import proofread_all_papers
from rank_papers import score_and_rank_papers

# On average there are about 150-250 papers per day & we want to look back two weeks
MAX_PER_DAY = 250
MAX_DAYS = 14
MAX_PER_CAT = MAX_PER_DAY * MAX_DAYS


# def compile_newsletter():
#     """Stitches all individual summaries into master Markdown and HTML files."""
#     print("\n--- COMPILING MASTER NEWSLETTER ---")
#     date_str = datetime.now().strftime("%Y-%m-%d")
#     master_md_file = f"AI_Digest_{date_str}.md"
#     master_html_file = f"AI_Digest_{date_str}.html"

#     summary_files = glob.glob(f"{OUTPUT_DIR}/**/summary.md", recursive=True)

#     if not summary_files:
#         print("No summaries found to compile.")
#         return

#     # Compile markdown master file
#     markdown_content = f"# AI Research Digest - {date_str}\n\n"
#     markdown_content += "> *Curated via Semantic Scholar Impact Metrics & Mistral*\n\n"
#     markdown_content += "---\n\n"

#     with open(master_md_file, "w", encoding="utf-8") as outfile:
#         outfile.write(markdown_content)
#         for file in summary_files:
#             with open(file, "r", encoding="utf-8") as infile:
#                 outfile.write(infile.read())
#                 outfile.write("\n\n---\n\n")

#     print(f"✅ Markdown newsletter compiled to: {master_md_file}")

#     # Compile HTML master file for Substack
#     html_content = markdown_content
#     for file in summary_files:
#         with open(file, "r", encoding="utf-8") as infile:
#             html_content += infile.read()
#             html_content += "\n\n---\n\n"

#     # Convert to beautiful HTML
#     html_output = markdown_to_html(html_content)
#     full_html = create_substack_post_html(
#         html_output, f"AI Research Digest - {date_str}"
#     )

#     with open(master_html_file, "w", encoding="utf-8") as outfile:
#         outfile.write(full_html)

#     print(f"✅ HTML newsletter compiled to: {master_html_file}")
#     print(
#         "\n📧 Ready for Substack! Copy the HTML file content and paste into Substack editor."
#     )


def filter_papers(papers, count):
    print(f"\n3. Filtering {len(papers)} papers to top {count}")
    return papers[:count]


def main():
    print("AI Daily Bytes processor\n")

    # 1. Fetch ALL papers from the last 14 days and deduplicate
    global_papers = fetch_all_recent_papers(
        days=MAX_DAYS, max_per_cat=MAX_PER_CAT, ignore_cache=False
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
    # proofread_all_papers(
    #     papers_date_folder, provider_type=MODEL_PROVIDER, **provider_config
    # )

    # 6. Compile the final product
    # compile_newsletter()


if __name__ == "__main__":
    main()
