"""Markdown content generator."""

import os
import re
import time
from typing import Any, Dict

from model_provider import get_model_provider
from pypdf import PdfReader
from schema import GeneratedContent, ProcessedItem

from generators.base import ContentGenerator


class MarkdownGenerator(ContentGenerator):
    """Generate markdown summaries from processed items."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.content_type = "markdown"
        self.template_name = config.get("template", "research_paper")
        self.template_path = config.get(
            "template_path", "templates/research_paper.yaml"
        )
        self.model_provider_type = config.get("model_provider", "ollama")
        self.model_config = config.get("model_config", {})
        self.output_dir = config.get("output_dir", "papers")
        self.max_retries = config.get("max_retries", 3)

        # Load template
        self.template = self._load_template()

    def generate(self, processed_item: ProcessedItem) -> GeneratedContent:
        """Generate markdown summary from processed item."""
        item = processed_item.item

        # Extract PDF text if available
        pdf_path = processed_item.processing_metadata.get("pdf_path")
        paper_text = ""

        if pdf_path and os.path.exists(pdf_path):
            paper_text = self._extract_pdf_text(pdf_path)

        # Format prompt
        prompt = self.template.format(
            title=item.title,
            domain=item.metadata.get("primary_category", "Unknown"),
            arxiv_url=item.metadata.get("entry_id", ""),
            paper_text=paper_text,
        )

        # Generate with model
        output_text = self._generate_with_model(prompt)

        return GeneratedContent(
            processed_item=processed_item,
            content_type=self.content_type,
            content=output_text,
            template_name=self.template_name,
            generation_metadata={
                "model_provider": self.model_provider_type,
                "template": self.template_name,
            },
        )

    def supports_template(self, template_name: str) -> bool:
        """Check if generator supports a template."""
        return template_name in ["research_paper", "default"]

    def _load_template(self) -> str:
        """Load template from file."""
        if os.path.exists(self.template_path):
            with open(self.template_path, "r") as f:
                return f.read()

        # Return default template if file not found
        return self._get_default_template()

    def _get_default_template(self) -> str:
        """Return default markdown template."""
        return """You are an expert AI researcher and technical reviewer. Read the following research paper and extract the crucial information to generate a markdown newsletter section.

CRITICAL FORMATTING RULES - YOU MUST FOLLOW THESE EXACTLY:
1. Output ONLY the markdown content. NO introductions, NO preamble, NO conversational text.
2. Start immediately with the title line: # [Domain]: [Catchy Headline]
3. Use ONLY Title Case for the headline (not small caps, not ALL CAPS).
4. ALWAYS include the [Domain] placeholder in the first line.
5. DO NOT include a bibliography, reference list, or citations at the end.
6. Stop generating text immediately after "The Verdict" line. Do not add anything after [END OF OUTPUT].
7. Use exactly the section headers provided below - do not modify them.
8. All scores MUST be in format: X/5 (e.g., 3/5, 4/5, 4.5/5).

CONTENT RULES:
9. ACTIVELY HUNT for GitHub, Project Page, or Hugging Face links.
10. ACTIVELY HUNT for hardware usage, training times, or GPU requirements.
11. Be highly critical but fair in your "AI Reviewer Scorecard". Do not give perfect scores unless the paper is a true breakthrough.
12. For "The Catch (Limitations)", include computational cost, dataset limitations, failure modes, and generalization concerns.
13. For "How Does This Compare", explain specific improvements over prior methods with quantitative comparisons when available.

Follow this EXACT markdown template (replace placeholders with actual content):

# [Domain]: [Catchy Headline about this Paper]

**[Read the full paper on arXiv]({arxiv_url})**

**TL;DR:** [One sentence that explains why this paper matters].

## 1. The Big Breakthrough: {title}
* **The Problem:** [1-2 sentences on the friction point].
* **The Solution:** [Describe the innovation in plain English].
* **The "Killer Metric":** [Most impressive result] (vs. [baseline] previously).
* **The Catch (Limitations):** [Main limitations including: computational cost, dataset biases, failure modes, generalization concerns].

## 2. How Does This Compare?
* **vs. [Prior Method 1]:** [Key improvement and quantitative difference if available].
* **vs. [Prior Method 2]:** [Key improvement and quantitative difference if available].

## 3. The "Deep End" (Technical Details)
* **For the engineers:** [Mention specific architectures, equations, or methods used].
* **Compute & Hardware:** [State the hardware/GPUs used, training time, memory requirements. If none, write "Compute requirements not explicitly provided"].
* **Code/Data Availability:** [EXTRACTED LINK TO GITHUB/PROJECT. If none, write "Not provided"].

## 4. Industry Application
* **Real-World Use Case:** [Suggest one specific, practical way a company or developer could use this today].
* **Best For:** [Target audience/domain - who should care about this paper?].

## 5. AI Reviewer's Scorecard
* **Novelty:** X/5 - [Is this a paradigm shift or an incremental improvement?].
* **Technical Rigor:** X/5 - [Are baselines strong and experiments thorough?].
* **Reproducibility:** X/5 - [Are code, data, and implementation details available?].
* **The Verdict:** [Must-Read/Skim/Skip] - [One sentence reason]. Best for [specific audience].

[END OF OUTPUT]

Here is the paper text:
{paper_text}
"""

    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF file."""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

            # Clean up text
            text = self._clean_paper_text(text)
            return text
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            return ""

    def _clean_paper_text(self, text: str) -> str:
        """Truncate text at References section."""
        match = re.search(
            r"\n\s*(References|Bibliography|REFERENCES|BIBLIOGRAPHY)\s*\n", text
        )
        if match:
            return text[: match.start()]
        return text

    def _generate_with_model(self, prompt: str) -> str:
        """Generate content using configured model provider."""
        model_provider = get_model_provider(
            self.model_provider_type, **self.model_config
        )

        for attempt in range(self.max_retries):
            try:
                output_text = model_provider.generate_summary(prompt)

                if not output_text.strip():
                    raise ValueError("Model returned empty response")

                return output_text

            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(5)
                else:
                    raise
