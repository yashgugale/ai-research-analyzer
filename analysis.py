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
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.get(pdf_url, timeout=60, stream=True)
                    response.raise_for_status()

                    # Write in chunks to handle large files
                    total_size = int(response.headers.get("content-length", 0))
                    downloaded_size = 0

                    with open(pdf_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)

                    # Verify download completed
                    if total_size > 0 and os.path.getsize(pdf_path) < total_size * 0.9:
                        print(
                            f"Incomplete download (attempt {attempt + 1}/{max_retries}), retrying..."
                        )
                        os.remove(pdf_path)
                        time.sleep(2)
                        continue

                    break  # Success
                except Exception as e:
                    print(
                        f"Failed to download PDF (attempt {attempt + 1}/{max_retries}): {e}"
                    )
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                    if attempt < max_retries - 1:
                        time.sleep(2)
                    else:
                        print(f"Failed to download PDF after {max_retries} attempts")
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
