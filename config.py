import os

# Create a papers directory if it doesn't exist
OUTPUT_DIR = "papers"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Create cache directory for storing daily paper fetches
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Model Provider Configuration
# Options: "ollama", "openai", "anthropic"
MODEL_PROVIDER = "ollama"

# Provider-specific configuration
MODEL_PROVIDER_CONFIG = {
    "ollama": {
        # "model_name": "llama3.2",
        "model_name": "mistral",
    },
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY"),  # Set via environment variable
        "model_name": "gpt-4",
    },
    "anthropic": {
        "api_key": os.getenv("ANTHROPIC_API_KEY"),  # Set via environment variable
        "model_name": "claude-3-opus-20240229",
    },
}


# Arxiv categories
CATEGORIES = {
    "cs.LG": "Machine Learning",  # Top 3
    "cs.CV": "Computer Vision",
    "cs.CL": "Computation and Language",
    "cs.MA": "Multiagent Systems",  # Next 3
    "cs.IR": "Information Retrieval",
    "eess.AS": "Audio and Speech Processing",
}


# The Markdown Template for the LLM
PROMPT_TEMPLATE = """
You are an expert AI researcher and technical reviewer. Read the following research paper and extract the crucial information to generate a markdown newsletter section.

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

**[Read the full paper on arXiv]({Arxiv_URL})**

**TL;DR:** [One sentence that explains why this paper matters].

## 1. The Big Breakthrough: {Title}
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
