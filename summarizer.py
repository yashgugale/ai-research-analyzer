import os
import re
import time

from config import MARKDOWN_TEMPLATE, PROMPT_TEMPLATE
from model_provider import get_model_provider
from pypdf import PdfReader


def clean_paper_text(text):
    """Truncates the text at the References or Bibliography section."""
    match = re.search(
        r"\n\s*(References|Bibliography|REFERENCES|BIBLIOGRAPHY)\s*\n", text
    )
    if match:
        return text[: match.start()]
    return text


def extract_text_from_pdf(pdf_path):
    """Reads a PDF and extracts all text."""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text


def generate_markdown_summary(
    paper_info, provider_type="ollama", force_regenerate=False, **provider_kwargs
):
    """
    Passes the paper text to a model provider and saves the markdown file.

    Args:
        paper_info: Dictionary with paper metadata (pdf_path, folder_path, title, domain, arxiv_url)
        provider_type: Type of model provider ('ollama', 'openai', 'anthropic')
        **provider_kwargs: Additional arguments to pass to the model provider
    """
    pdf_path = paper_info["pdf_path"]
    folder_path = paper_info["folder_path"]
    title = paper_info["title"]
    domain = paper_info["domain"]
    arxiv_url = paper_info["arxiv_url"]
    paper_id = paper_info["id"]

    # Check if summary already exists
    md_path = os.path.join(folder_path, f"{paper_id}_summary.md")
    if os.path.exists(md_path) and not force_regenerate:
        print("Summary already exists, skipping generation")
        return

    print("Extracting text")
    raw_paper_text = extract_text_from_pdf(pdf_path)
    clean_text = clean_paper_text(raw_paper_text)
    markdown_template = MARKDOWN_TEMPLATE.format(
        Domain=domain,
        Title=title,
        Arxiv_URL=arxiv_url,
    )
    prompt = PROMPT_TEMPLATE.format(
        paper_text=clean_text,
        Markdown_Template=markdown_template,
    )

    print("Generating analysis")

    # Get the model provider
    model_provider = get_model_provider(provider_type, **provider_kwargs)

    # Retry logic: Try up to 3 times if model fails or returns empty
    max_retries = 3
    for attempt in range(max_retries):
        try:
            output_text = model_provider.generate_summary(prompt)

            if not output_text.strip():
                raise ValueError("Model returned an empty response.")

            md_path = os.path.join(folder_path, f"{paper_id}_summary.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(output_text)

            print("Analysis complete")

            return  # Success, exit the retry loop

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print("Retrying in 5 seconds...")
                time.sleep(5)
            else:
                print("Failed to generate analysis after 3 attempts.")
