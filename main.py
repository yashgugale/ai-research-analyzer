import glob
import time
from datetime import datetime

from arxiv_fetcher import download_paper, fetch_all_recent_papers, score_and_rank_papers
from config import MODEL_PROVIDER, MODEL_PROVIDER_CONFIG, OUTPUT_DIR
from markdown_to_html import create_substack_post_html, markdown_to_html
from summarizer import generate_markdown_summary


def compile_newsletter():
    """Stitches all individual summaries into master Markdown and HTML files."""
    print("\n--- COMPILING MASTER NEWSLETTER ---")
    date_str = datetime.now().strftime("%Y-%m-%d")
    master_md_file = f"AI_Digest_{date_str}.md"
    master_html_file = f"AI_Digest_{date_str}.html"

    summary_files = glob.glob(f"{OUTPUT_DIR}/**/summary.md", recursive=True)

    if not summary_files:
        print("No summaries found to compile.")
        return

    # Compile markdown master file
    markdown_content = f"# AI Research Digest - {date_str}\n\n"
    markdown_content += "> *Curated via Semantic Scholar Impact Metrics & Mistral*\n\n"
    markdown_content += "---\n\n"

    with open(master_md_file, "w", encoding="utf-8") as outfile:
        outfile.write(markdown_content)
        for file in summary_files:
            with open(file, "r", encoding="utf-8") as infile:
                outfile.write(infile.read())
                outfile.write("\n\n---\n\n")

    print(f"✅ Markdown newsletter compiled to: {master_md_file}")

    # Compile HTML master file for Substack
    html_content = markdown_content
    for file in summary_files:
        with open(file, "r", encoding="utf-8") as infile:
            html_content += infile.read()
            html_content += "\n\n---\n\n"

    # Convert to beautiful HTML
    html_output = markdown_to_html(html_content)
    full_html = create_substack_post_html(
        html_output, f"AI Research Digest - {date_str}"
    )

    with open(master_html_file, "w", encoding="utf-8") as outfile:
        outfile.write(full_html)

    print(f"✅ HTML newsletter compiled to: {master_html_file}")
    print(
        "\n📧 Ready for Substack! Copy the HTML file content and paste into Substack editor."
    )


def main():
    print("Starting AI Research Digest Pipeline...\n")

    # 1. Fetch ALL papers from the last 14 days and deduplicate
    global_papers = fetch_all_recent_papers(days=14)

    # 2. Score and Rank them globally
    ranked_papers = score_and_rank_papers(global_papers)

    # 3. Select top 14 papers from global ranking and summarize
    print("\n--- SELECTING TOP 14 & SUMMARIZING ---")

    top_14_papers = ranked_papers[:14]

    for idx, paper_data in enumerate(top_14_papers, 1):
        paper = paper_data["paper"]
        score = paper_data["score"]
        categories = paper_data.get("categories", [])
        category_code = categories[0] if categories else "Unknown"

        # Handle both arxiv objects (fresh) and cached dictionaries
        paper_title = (
            paper.title if hasattr(paper, "title") else paper.get("title", "Unknown")
        )
        print(f"\n#{idx} 🏆 {paper_title} (Score: {score:.2f}) [{category_code}]")

        # Download and Summarize
        try:
            paper_info = download_paper(paper, category_code)
            # Get provider config for the current model provider
            provider_config = MODEL_PROVIDER_CONFIG.get(MODEL_PROVIDER, {})
            generate_markdown_summary(
                paper_info, provider_type=MODEL_PROVIDER, **provider_config
            )
            time.sleep(2)  # Give your local system a brief rest between generations
        except Exception as e:
            print(f"Error summarizing {paper_title}: {e}")

    # 4. Compile the final product
    compile_newsletter()


if __name__ == "__main__":
    main()
