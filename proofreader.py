import json
import os
import re

from config import MARKDOWN_TEMPLATE
from model_provider import get_model_provider


def extract_sections_from_markdown(markdown_text):
    """Extract all sections from markdown to validate structure."""
    sections = {
        "title": None,
        "arxiv_link": None,
        "tldr": None,
        "big_breakthrough": None,
        "comparison": None,
        "technical_details": None,
        "industry_application": None,
        "scorecard": None,
    }

    # Extract title (# Domain: Headline)
    title_match = re.search(r"^#\s+(.+?):\s+(.+?)$", markdown_text, re.MULTILINE)
    if title_match:
        sections["title"] = (title_match.group(1), title_match.group(2))

    # Extract arXiv link
    arxiv_match = re.search(r"\[Read the full paper on arXiv\]\((.+?)\)", markdown_text)
    if arxiv_match:
        sections["arxiv_link"] = arxiv_match.group(1)

    # Extract TL;DR
    tldr_match = re.search(
        r"\*\*TL;DR:\*\*\s+(.+?)(?=\n\n##|\Z)", markdown_text, re.DOTALL
    )
    if tldr_match:
        sections["tldr"] = tldr_match.group(1).strip()

    # Extract section 1: Big Breakthrough
    section1_match = re.search(
        r"##\s+1\.\s+The Big Breakthrough:.+?(?=\n##\s+2\.|\Z)",
        markdown_text,
        re.DOTALL,
    )
    if section1_match:
        sections["big_breakthrough"] = section1_match.group(0)

    # Extract section 2: How Does This Compare
    section2_match = re.search(
        r"##\s+2\.\s+How Does This Compare\?.+?(?=\n##\s+3\.|\Z)",
        markdown_text,
        re.DOTALL,
    )
    if section2_match:
        sections["comparison"] = section2_match.group(0)

    # Extract section 3: Technical Details
    section3_match = re.search(
        r'##\s+3\.\s+The "Deep End".+?(?=\n##\s+4\.|\Z)',
        markdown_text,
        re.DOTALL,
    )
    if section3_match:
        sections["technical_details"] = section3_match.group(0)

    # Extract section 4: Industry Application
    section4_match = re.search(
        r"##\s+4\.\s+Industry Application.+?(?=\n##\s+5\.|\Z)",
        markdown_text,
        re.DOTALL,
    )
    if section4_match:
        sections["industry_application"] = section4_match.group(0)

    # Extract section 5: Scorecard
    section5_match = re.search(
        r"##\s+5\.\s+AI Reviewer's Scorecard.+?(?=\Z)",
        markdown_text,
        re.DOTALL,
    )
    if section5_match:
        sections["scorecard"] = section5_match.group(0)

    return sections


def validate_markdown_structure(markdown_text):
    """Validate that markdown adheres to the template structure."""
    issues = []
    score = 10

    sections = extract_sections_from_markdown(markdown_text)

    # Check title format
    if not sections["title"]:
        issues.append("Missing or malformed title (# Domain: Headline)")
        score -= 1.5
    else:
        domain, headline = sections["title"]
        if not domain or not headline:
            issues.append("Title missing domain or headline")
            score -= 0.5

    # Check arXiv link
    if not sections["arxiv_link"]:
        issues.append("Missing arXiv link")
        score -= 1

    # Check TL;DR
    if not sections["tldr"]:
        issues.append("Missing TL;DR section")
        score -= 1
    elif len(sections["tldr"]) < 20:
        issues.append("TL;DR too short (should be at least one sentence)")
        score -= 0.5

    # Check all required sections exist
    required_sections = [
        ("big_breakthrough", "## 1. The Big Breakthrough"),
        ("comparison", "## 2. How Does This Compare"),
        ("technical_details", '## 3. The "Deep End"'),
        ("industry_application", "## 4. Industry Application"),
        ("scorecard", "## 5. AI Reviewer's Scorecard"),
    ]

    for section_key, section_name in required_sections:
        if not sections[section_key]:
            issues.append(f"Missing section: {section_name}")
            score -= 1.5

    # Check for required subsections in Big Breakthrough
    if sections["big_breakthrough"]:
        required_items = [
            "**The Problem:**",
            "**The Solution:**",
            "**The Killer Metric:**",
            "**The Catch (Limitations):**",
        ]
        for item in required_items:
            if item not in sections["big_breakthrough"]:
                issues.append(f"Missing '{item}' in Big Breakthrough section")
                score -= 0.75

    # Check for required subsections in Comparison
    if sections["comparison"]:
        if "**vs." not in sections["comparison"]:
            issues.append("Missing comparison items (vs. Prior Method) in section 2")
            score -= 1

    # Check for required subsections in Technical Details
    if sections["technical_details"]:
        required_items = [
            "**For the engineers:**",
            "**Compute & Hardware:**",
            "**Code/Data Availability:**",
        ]
        for item in required_items:
            if item not in sections["technical_details"]:
                issues.append(f"Missing '{item}' in Technical Details section")
                score -= 0.75

    # Check for required subsections in Industry Application
    if sections["industry_application"]:
        required_items = [
            "**Real-World Use Case:**",
            "**Best For:**",
        ]
        for item in required_items:
            if item not in sections["industry_application"]:
                issues.append(f"Missing '{item}' in Industry Application section")
                score -= 0.75

    # Check for required subsections in Scorecard
    if sections["scorecard"]:
        required_items = [
            "**Novelty:**",
            "**Technical Rigor:**",
            "**Reproducibility:**",
            "**The Verdict:**",
        ]
        for item in required_items:
            if item not in sections["scorecard"]:
                issues.append(f"Missing '{item}' in Scorecard section")
                score -= 0.75

    # Check for score format (X/5)
    if sections["scorecard"]:
        score_pattern = r"\d+(?:\.\d+)?/5"
        if not re.search(score_pattern, sections["scorecard"]):
            issues.append("Missing or malformed scores (should be X/5 format)")
            score -= 1

    # Check for [END OF OUTPUT] marker (should not be present)
    if "[END OF OUTPUT]" in markdown_text:
        issues.append("Contains [END OF OUTPUT] marker (should be removed)")
        score -= 1

    # Check for unwanted markers or tags
    unwanted_markers = [
        r"\[.*?\](?!\()",  # [anything] that's not a link
        r"<.*?>",  # HTML tags
    ]
    for marker_pattern in unwanted_markers:
        if re.search(marker_pattern, markdown_text):
            matches = re.findall(marker_pattern, markdown_text)
            if any(
                m
                not in [
                    "[Read the full paper on arXiv]",
                    "[Must-Read",
                    "[Skim",
                    "[Skip",
                ]
                for m in matches
            ):
                issues.append(f"Contains unwanted markers: {set(matches)}")
                score -= 0.5
                break

    # Ensure score doesn't go below 0
    score = max(0, score)

    return {
        "score": round(score, 2),
        "issues": issues,
        "sections_found": sum(1 for v in sections.values() if v),
        "total_sections": len(sections),
    }


def proofread_markdown(
    paper_id, markdown_path, provider_type="ollama", **provider_kwargs
):
    """
    Proofread a markdown file and assign a quality score.
    Uses an AI model to validate structure and content quality.
    """
    if not os.path.exists(markdown_path):
        return {
            "paper_id": paper_id,
            "score": 0,
            "status": "error",
            "message": f"Markdown file not found: {markdown_path}",
        }

    # Read the markdown file
    with open(markdown_path, "r", encoding="utf-8") as f:
        markdown_content = f.read()

    # Perform structural validation
    validation_result = validate_markdown_structure(markdown_content)

    # If structural score is very low, return early
    if validation_result["score"] < 3:
        return {
            "paper_id": paper_id,
            "score": validation_result["score"],
            "status": "failed",
            "issues": validation_result["issues"],
            "validation_details": validation_result,
        }

    # Use AI model to validate content quality and adherence to guidelines
    proofreading_prompt = f"""You are a quality assurance expert. Review the following markdown content and check if it adheres to the template structure and guidelines.

TEMPLATE STRUCTURE:
{MARKDOWN_TEMPLATE}

VALIDATION CRITERIA:
1. All required sections are present and properly formatted
2. Content is accurate and well-written
3. No placeholder text remains (e.g., [1-2 sentences...])
4. Scores are in X/5 format
5. No unwanted markers or tags
6. Content flows logically and is engaging
7. Technical details are accurate and relevant
8. Comparisons with prior methods are specific and quantitative

MARKDOWN CONTENT TO REVIEW:
{markdown_content}

Provide a JSON response with:
- "quality_score": integer from 0-10 (0=completely broken, 10=perfect)
- "issues": list of specific issues found (empty if none)
- "suggestions": list of improvement suggestions (empty if none)
- "overall_assessment": brief summary of the quality

Respond ONLY with valid JSON, no other text."""

    try:
        model_provider = get_model_provider(provider_type, **provider_kwargs)
        ai_response = model_provider.generate_summary(proofreading_prompt)

        # Parse AI response
        json_match = re.search(r"\{.*\}", ai_response, re.DOTALL)
        if json_match:
            ai_result = json.loads(json_match.group(0))
            ai_score = ai_result.get("quality_score", validation_result["score"])
        else:
            ai_score = validation_result["score"]

        # Combine structural and AI scores (weighted average)
        final_score = round((validation_result["score"] * 0.4 + ai_score * 0.6), 2)

        return {
            "paper_id": paper_id,
            "score": final_score,
            "status": "passed" if final_score >= 7 else "needs_review",
            "structural_score": validation_result["score"],
            "ai_score": ai_score,
            "structural_issues": validation_result["issues"],
            "ai_feedback": ai_result if json_match else None,
        }

    except Exception as e:
        # If AI proofreading fails, use structural score only
        return {
            "paper_id": paper_id,
            "score": validation_result["score"],
            "status": "passed" if validation_result["score"] >= 7 else "needs_review",
            "structural_score": validation_result["score"],
            "ai_score": None,
            "structural_issues": validation_result["issues"],
            "error": str(e),
        }


def proofread_all_papers(papers_date_folder, provider_type="ollama", **provider_kwargs):
    """
    Proofread all markdown files in a date folder and save scores to JSON.
    Returns list of proofreading results.
    """
    if not os.path.exists(papers_date_folder):
        print(f"Folder not found: {papers_date_folder}")
        return []

    results = []
    markdown_files = []

    # Find all markdown summary files
    for root, dirs, files in os.walk(papers_date_folder):
        for file in files:
            if file.endswith("_summary.md"):
                markdown_files.append(os.path.join(root, file))

    if not markdown_files:
        print(f"No markdown files found in {papers_date_folder}")
        return []

    print(f"\n--- PROOFREADING {len(markdown_files)} PAPERS ---")

    for markdown_path in markdown_files:
        # Extract paper_id from filename
        filename = os.path.basename(markdown_path)
        paper_id = filename.replace("_summary.md", "")

        print(f"Proofreading {paper_id}...", end=" ")

        result = proofread_markdown(
            paper_id, markdown_path, provider_type=provider_type, **provider_kwargs
        )
        results.append(result)

        print(f"Score: {result['score']}/10 - {result['status']}")

    # Save results to JSON
    results_file = os.path.join(papers_date_folder, "proofreading_results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Proofreading results saved to: {results_file}")

    # Print summary
    avg_score = sum(r["score"] for r in results) / len(results) if results else 0
    passed = sum(1 for r in results if r["status"] == "passed")
    needs_review = sum(1 for r in results if r["status"] == "needs_review")

    print("\nSummary:")
    print(f"  Average Score: {avg_score:.2f}/10")
    print(f"  Passed: {passed}/{len(results)}")
    print(f"  Needs Review: {needs_review}/{len(results)}")

    return results
