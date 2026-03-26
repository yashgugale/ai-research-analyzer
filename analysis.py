import os
import time
from datetime import date

import requests
from config import ALL_CATEGORIES, MODEL_PROVIDER, MODEL_PROVIDER_CONFIG, OUTPUT_DIR
from slugify import slugify
from summarizer import generate_markdown_summary


def download_paper(paper, raw_category_code):
    """Helper function to format folders and download the PDF."""

    clean_id = paper["entry_id"].split("/abs/")[-1].split("v")[0]
    title = paper["title"]
    entry_id = paper["entry_id"]
    pdf_url = paper.get("pdf_url")
    category_code = slugify(raw_category_code)

    folder_name = f"{date.today().strftime('%Y-%m-%d')}/{category_code}"
    folder_path = os.path.join(OUTPUT_DIR, folder_name)

    os.makedirs(folder_path, exist_ok=True)

    pdf_path = os.path.join(folder_path, f"{clean_id}.pdf")
    if not os.path.exists(pdf_path):
        if pdf_url:
            try:
                response = requests.get(pdf_url, timeout=30)
                response.raise_for_status()
                with open(pdf_path, "wb") as f:
                    f.write(response.content)
                # print(f"Downloaded PDF to: {pdf_path}")
            except Exception as e:
                print(f"Failed to download PDF: {e}")
        else:
            print("No PDF URL available")
    else:
        print(f"PDF already exists in: {pdf_path}")

    paper_info = {
        "title": title,
        "id": clean_id,
        "domain": ALL_CATEGORIES[raw_category_code],
        "folder_path": folder_path,
        "pdf_path": pdf_path,
        "arxiv_url": entry_id,
        "arxiv_id": clean_id,
    }

    return paper_info


def analyze_papers(top_papers, force_regenerate=False):

    print("\n4. Analyzing top papers")
    for idx, paper in enumerate(top_papers, 1):
        score = paper.get("score", 0)
        category_code = paper.get("primary_category", "Unknown")
        paper_title = paper.get("title", "Unknown")

        print(f"\n#{idx} 🏆 {paper_title} (Score: {score:.2f}) [{category_code}]")

        # Download and Summarize
        try:
            paper_info = download_paper(paper, category_code)
            # Get provider config for the current model provider
            provider_config = MODEL_PROVIDER_CONFIG.get(MODEL_PROVIDER, {})
            generate_markdown_summary(
                paper_info,
                provider_type=MODEL_PROVIDER,
                force_regenerate=force_regenerate,
                **provider_config,
            )
            time.sleep(2)  # Give your local system a brief rest between generations
        except Exception as e:
            print(f"Error summarizing {paper_title}: {e}")
