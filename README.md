# AI Daily Bytes - Automated AI Research Paper Digest

## 1. Introduction

**AI Daily Bytes** is an automated system that curates, analyzes, and publishes the most impactful AI research papers to Substack. The system fetches papers from arXiv, ranks them based on citation metrics and research impact, generates AI-powered summaries, and automatically schedules them for publication.

This tool is designed for researchers, AI enthusiasts, and newsletter subscribers who want to stay updated with high-impact AI research without the information overload. Instead of sifting through hundreds of papers daily, AI Daily Bytes delivers the top 7 papers from the previous week, each with a concise, AI-generated summary.

### Key Features

- **Intelligent Paper Ranking**: Papers are ranked based on citation counts, influential citations, and reference counts
- **Automated Summarization**: Uses LLM (Mistral/Ollama) to generate concise, readable summaries
- **Citation Accumulation**: Fetches papers from 7-14 days ago to ensure they have accumulated meaningful citations
- **Substack Integration**: Automatically publishes papers to Substack with scheduled release times
- **Multi-Category Support**: Covers top 6 arXiv categories in AI/ML
- **Caching & Optimization**: Implements intelligent caching to avoid redundant API calls

### Substack publication

[AI Daily Bytes](https://aidailybytes.substack.com)

**Note**: The paper summary is created using an LLM system. It is possible that there are some inaccuracies in the summary or formatting issues. Please refer to the original paper for the most accurate information.
Experiment with different models to improve the quality of the summaries.

### Improvements

- The ranking algorithm can be improved to accommodate for affiliations and institutions to better identify impactful research
- The LLM currently ignores images and tables in the papers and runs on text only data. This can be improved by using a multimodal LLM.
- Potential improvements to the prompt system to improve the quality of the summaries
- Use better filtering criteria to identify impactful papers
---

## 2. How It Works

The system follows a 6-step pipeline:

### Step 1: Fetch Papers from arXiv
- Fetches papers from the **week prior** (7-14 days ago) across 6 categories
- Deduplicates papers across categories
- Caches results to avoid redundant API calls
- **Why the week prior?** Papers need time to accumulate citations and demonstrate real impact. Papers that are too new may not have meaningful citation counts yet and could be missed even though they have relevant content. We also want to avoid papers that are too old. 

### Step 2: Score and Rank Papers
Papers are ranked using a quality score formula:
```
Score = (influential_citations × 3) + citation_count + (references × 0.01)
```
- **Influential Citations**: Highly weighted (3x multiplier) as they indicate significant impact
- **Citation Count**: Direct measure of research impact
- **References**: Indicates how comprehensive the research is

### Step 3: Filter Top Papers
Selects the top 7 papers from the ranked list for analysis and publication.

### Step 4: Generate Summaries
- Downloads PDF from arXiv with retry logic for failed downloads
- Extracts text from PDF
- Uses LLM (Mistral via Ollama) to generate structured markdown summaries
- Summaries include: Overview, Key Contributions, TL;DR, and Code/Data Availability

### Step 5: Proofread Summaries
- Reviews generated summaries for quality and accuracy
- Fixes formatting issues and improves readability
- Ensures consistent tone and structure

### Step 6: Publish to Substack
- Converts markdown to Substack's document JSON format
- Creates drafts on Substack
- Schedules publication for the next day at 10am EST
- Posts are scheduled 24 hours apart

---

## 3. Setup

### Prerequisites

- Python 3.8+
- Ollama with Mistral model installed (for local LLM)
- Substack account with API access
- arXiv API access (no authentication required)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yashgugale/ai-research-analyzer.git
   cd ai-research-analyzer
   ```

2. **Create a virtual environment**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   uv pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   # Substack API Configuration
   COOKIES_STRING=<your-substack-cookies>
   PUBLICATION_URL=https://aidailybytes.substack.com
   
   # Model Configuration
   MODEL_PROVIDER=ollama  # or openai, anthropic, etc.
   OLLAMA_MODEL=mistral
   OLLAMA_BASE_URL=http://localhost:11434
   ```

5. **Start Ollama**
   ```bash
   ollama serve
   # In another terminal:
   ollama pull mistral
   ```

6. **Verify setup**
   ```bash
   python3 -c "from fetch_arxiv_papers import fetch_all_recent_papers; print('✅ Setup complete!')"
   ```

### Configuration

Edit `config.py` to customize:
- **Categories**: Modify `FILTER_CATEGORIES` to select which arXiv categories to monitor
- **Model Provider**: Change `MODEL_PROVIDER` to use different LLMs (ollama, openai, anthropic)
- **Output Directory**: Set `OUTPUT_DIR` for where to save papers and summaries
- **Cache Directory**: Configure `CACHE_DIR` for caching

### Running the System

**One-time execution:**
```bash
python3 main.py
```

### Output Structure

```
papers/
├── 2026-03-30/
│   ├── cs-cv/
│   │   ├── 2603.18423.pdf
│   │   └── 2603.18423_summary.md
│   ├── cs-lg/
│   └── ...
└── cache/
    ├── paper_metadata/
    │   └── 2026-03-30.json
    └── paper_ranked/
        └── 2026-03-30.json
```

### Troubleshooting

**Issue: "No papers fetched"**
- Check arXiv API connectivity
- Verify date range in `main.py` (should be 7-14 days back)
- Clear cache: `rm -rf cache/`

**Issue: PDF download failures**
- System automatically retries up to 3 times
- Check internet connection and arXiv availability
- Some PDFs may be unavailable

**Issue: Substack publishing fails**
- Verify `COOKIES_STRING` is current (Substack cookies expire)
- Check `PUBLICATION_URL` is correct
- Ensure Substack API is accessible

---

## 4. Contact & Feedback

For questions, bug reports, or feature requests:

📧 **Email**: yashgugale@gmail.com


---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Daily Bytes Pipeline                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Fetch Papers (arXiv)                                     │
│     └─> Deduplicate & Cache                                 │
│                                                               │
│  2. Score & Rank                                             │
│     └─> Citation-based quality metrics                      │
│                                                               │
│  3. Filter Top 7                                             │
│     └─> Select highest-scoring papers                       │
│                                                               │
│  4. Analyze & Summarize                                      │
│     └─> Download PDF → Extract Text → LLM Summary           │
│                                                               │
│  5. Proofread                                                │
│     └─> Quality check & formatting                          │
│                                                               │
│  6. Publish to Substack                                      │
│     └─> Schedule for next day 10am EST                       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

**Last Updated**: March 30, 2026
