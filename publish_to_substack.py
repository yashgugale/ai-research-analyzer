import json
import os
import re

import requests
from dotenv import load_dotenv
from substack import Api
from substack.post import Post

load_dotenv()

api = None


def initialize_api():
    """Initialize Substack API connection."""
    global api
    if api is None:
        try:
            api = Api(
                cookies_string=os.getenv("COOKIES_STRING"),
                publication_url=os.getenv("PUBLICATION_URL"),
            )
            print("✅ Successfully authenticated with Substack")
        except Exception as e:
            print(f"❌ Failed to authenticate with Substack: {e}")
            raise
    return api


def get_all_drafts(offset: int = 0, limit: int = 25) -> dict:
    """
    Get all drafts from Substack.

    Args:
        offset: Number of drafts to skip (default: 0)
        limit: Number of drafts to return (default: 25)

    Returns:
        Dictionary with drafts list and metadata
    """
    try:
        publication_url = os.getenv("PUBLICATION_URL")
        url = f"{publication_url}/api/v1/post_management/drafts"
        params = {
            "offset": offset,
            "limit": limit,
            "order_by": "draft_updated_at",
            "order_direction": "desc",
        }
        headers = {"Cookie": os.getenv("COOKIES_STRING")}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching drafts: {e}")
        return {"error": str(e)}


def delete_draft(draft_id: str) -> dict:
    """
    Delete a draft by ID.

    Args:
        draft_id: The ID of the draft to delete

    Returns:
        Dictionary with deletion result
    """
    try:
        publication_url = os.getenv("PUBLICATION_URL")
        url = f"{publication_url}/api/v1/drafts/{draft_id}"
        headers = {"Cookie": os.getenv("COOKIES_STRING")}
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        print(f"✅ Draft {draft_id} deleted successfully")
        return {"status": "success", "draft_id": draft_id}
    except Exception as e:
        print(f"❌ Error deleting draft {draft_id}: {e}")
        return {"status": "error", "draft_id": draft_id, "error": str(e)}


def schedule_draft(
    draft_id: str,
    publish_date: str,
    post_audience: str = "everyone",
    email_audience: str = "everyone",
) -> dict:
    """
    Schedule a draft for publication.

    Args:
        draft_id: The ID of the draft to schedule
        publish_date: ISO 8601 datetime string (e.g., "2026-03-30T15:54:00.000Z")
        post_audience: Who can read the post on the web (default: "everyone")
        email_audience: Who receives the email notification (default: "everyone")

    Returns:
        Dictionary with scheduling result
    """
    try:
        publication_url = os.getenv("PUBLICATION_URL")
        url = f"{publication_url}/api/v1/drafts/{draft_id}/scheduled_release"
        headers = {
            "Cookie": os.getenv("COOKIES_STRING"),
            "Content-Type": "application/json",
        }
        payload = {
            "trigger_at": publish_date,
            "post_audience": post_audience,
            "email_audience": email_audience,
        }
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"✅ Draft {draft_id} scheduled for {publish_date}")
        return {"status": "success", "draft_id": draft_id, "publish_date": publish_date}
    except Exception as e:
        print(f"❌ Error scheduling draft {draft_id}: {e}")
        return {"status": "error", "draft_id": draft_id, "error": str(e)}


def extract_title_from_markdown(markdown_content: str) -> str:
    """Extract the title from markdown (first # heading)."""
    # Allow optional leading whitespace before the #
    match = re.search(r"^\s*#\s+(.+?)$", markdown_content, re.MULTILINE)
    if match:
        title = match.group(1).strip()
        # Remove any markdown formatting from title
        title = re.sub(r"\*\*(.+?)\*\*", r"\1", title)  # Remove bold
        title = re.sub(r"\*(.+?)\*", r"\1", title)  # Remove italic
        return title
    return "Untitled Paper Analysis"


def extract_subtitle_from_markdown(markdown_content: str) -> str:
    """Extract the TL;DR as subtitle."""
    # Match **TL;DR:** followed by text until double newline
    match = re.search(r"\*\*TL;DR:\*\*\s+(.+?)(?=\n\n)", markdown_content, re.DOTALL)
    if match:
        tldr = match.group(1).strip()
        # Remove any trailing punctuation and limit to 160 characters
        tldr = tldr.rstrip(".,;:")
        return tldr[:160] if len(tldr) > 160 else tldr
    return "AI Research Paper Analysis"


def parse_markdown_to_substack_doc(markdown_content: str) -> dict:
    """
    Parse markdown to Substack's document format.
    Properly handles headings, paragraphs, lists, bold, italic, and links.
    Skips the title line (first H1) but includes all other content.
    """
    lines = markdown_content.split("\n")
    content = []
    current_list_items = []

    i = 0
    title_skipped = False

    while i < len(lines):
        line = lines[i]

        # Skip the title line (first # heading only, not ## or ###)
        if not title_skipped and re.match(r"^\s*#\s+(?!#)", line):
            title_skipped = True
            i += 1
            continue

        # Skip empty lines between sections
        if not line.strip():
            # Flush any pending list items
            if current_list_items:
                content.append({"type": "bullet_list", "content": current_list_items})
                current_list_items = []
            i += 1
            continue

        # Handle headings - check for # at start of line (## and ### only, since # is skipped)
        heading_match = re.match(r"^\s*(#{2,3})\s+(.+)$", line)
        if heading_match:
            if current_list_items:
                content.append({"type": "bullet_list", "content": current_list_items})
                current_list_items = []
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()
            content.append(
                {
                    "type": "heading",
                    "attrs": {"level": level},
                    "content": parse_inline_markdown(heading_text),
                }
            )
            i += 1
        # Handle bullet points
        elif line.strip().startswith("* "):
            item_text = line.strip()[2:].strip()

            # Check if this line contains multiple bullet points combined
            # Specifically look for patterns like "**X:** ... Code/Data Availability: ..."
            # Only split if "Code/Data Availability:" appears AFTER other content (not at the start)
            cda_index = item_text.find("Code/Data Availability:")
            if cda_index > 0 and not item_text.startswith("**Code/Data Availability:"):
                # This is a combined bullet point - split it
                # Add the first part as a list item (everything before "Code/Data Availability:")
                first_part = item_text[:cda_index].rstrip(". ")
                current_list_items.append(
                    {
                        "type": "list_item",
                        "content": parse_inline_markdown(first_part),
                    }
                )
                # Add the second part as a separate list item with bold formatting preserved
                # Include everything from "Code/Data Availability:" onwards
                cda_content = item_text[
                    cda_index + len("Code/Data Availability:") :
                ].strip()
                # Remove link syntax if present (e.g., [text](url) -> text)
                cda_content = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cda_content)
                second_part = "**Code/Data Availability:** " + cda_content
                current_list_items.append(
                    {
                        "type": "list_item",
                        "content": parse_inline_markdown(second_part),
                    }
                )
            else:
                # Normal single bullet point
                current_list_items.append(
                    {
                        "type": "list_item",
                        "content": parse_inline_markdown(item_text),
                    }
                )
            i += 1
        # Handle paragraphs (including TL;DR)
        else:
            if current_list_items:
                content.append({"type": "bullet_list", "content": current_list_items})
                current_list_items = []
            content.append(
                {"type": "paragraph", "content": parse_inline_markdown(line.strip())}
            )
            i += 1

    # Flush any remaining list items
    if current_list_items:
        content.append({"type": "bullet_list", "content": current_list_items})

    return {"type": "doc", "content": content}


def parse_inline_markdown(text: str) -> list:
    """
    Parse inline markdown elements (bold, italic, links) into Substack format.
    Returns a list of text and mark objects.
    Handles nested formatting like **[link](url)**.
    """
    content = []
    pos = 0

    # Find all markdown elements with their positions
    elements = []

    # Find all bold **text** first (may contain links inside)
    bold_ranges = []
    for match in re.finditer(r"\*\*(.+?)\*\*", text):
        inner_text = match.group(1)
        bold_ranges.append((match.start(), match.end()))
        elements.append(
            {
                "start": match.start(),
                "end": match.end(),
                "type": "bold",
                "inner_text": inner_text,
            }
        )

    # Find all links [text](url) - skip if inside bold
    for match in re.finditer(r"\[([^\]]+)\]\(([^\)]+)\)", text):
        # Check if this link is inside any bold block
        is_inside_bold = any(
            bold_start < match.start() and match.end() < bold_end
            for bold_start, bold_end in bold_ranges
        )
        if not is_inside_bold:
            elements.append(
                {
                    "start": match.start(),
                    "end": match.end(),
                    "type": "link",
                    "text": match.group(1),
                    "href": match.group(2),
                }
            )

    # Find all italic *text* (only if not part of bold or link)
    for match in re.finditer(r"\*([^\*]+)\*", text):
        # Check if this overlaps with any existing element
        overlaps = any(
            e["start"] <= match.start() < e["end"]
            or e["start"] < match.end() <= e["end"]
            for e in elements
        )
        if not overlaps:
            elements.append(
                {
                    "start": match.start(),
                    "end": match.end(),
                    "type": "italic",
                    "text": match.group(1),
                }
            )

    # Sort elements by start position
    elements.sort(key=lambda x: x["start"])

    # Build content array
    pos = 0
    for elem in elements:
        # Add text before this element
        if elem["start"] > pos:
            before_text = text[pos : elem["start"]]
            if before_text:
                content.append({"type": "text", "text": before_text})

        # Add the element
        if elem["type"] == "bold":
            # Check if the inner text contains a link
            inner_text = elem["inner_text"]
            link_match = re.search(r"\[([^\]]+)\]\(([^\)]+)\)", inner_text)
            if link_match:
                # Bold with link inside
                content.append(
                    {
                        "type": "text",
                        "text": link_match.group(1),
                        "marks": [
                            {"type": "strong"},
                            {"type": "link", "attrs": {"href": link_match.group(2)}},
                        ],
                    }
                )
            else:
                # Just bold
                content.append(
                    {"type": "text", "text": inner_text, "marks": [{"type": "strong"}]}
                )
        elif elem["type"] == "link":
            content.append(
                {
                    "type": "text",
                    "text": elem["text"],
                    "marks": [{"type": "link", "attrs": {"href": elem["href"]}}],
                }
            )
        elif elem["type"] == "italic":
            content.append(
                {"type": "text", "text": elem["text"], "marks": [{"type": "em"}]}
            )

        pos = elem["end"]

    # Add remaining text
    if pos < len(text):
        remaining = text[pos:]
        if remaining:
            content.append({"type": "text", "text": remaining})

    # If no content was added, return the original text
    if not content:
        content = [{"type": "text", "text": text}]

    return content


def post_to_substack(
    markdown_content: str, paper_id: str = None, publish_at: str = None
) -> dict:
    """
    Create a Substack draft from markdown content.

    Args:
        markdown_content: The markdown content to post
        paper_id: Optional paper ID for tracking
        publish_at: Optional ISO 8601 datetime string to schedule publication (e.g., "2026-03-27T14:30:00Z")
                   If None, creates a draft. If provided, schedules the post for that time.

    Returns:
        Dictionary with post creation result
    """
    try:
        api = initialize_api()
        user_id = api.get_user_id()
        print(f"User ID: {user_id}")

        # Extract title and subtitle from markdown
        title = extract_title_from_markdown(markdown_content)
        # subtitle = extract_subtitle_from_markdown(markdown_content)

        if publish_at:
            print(f"Scheduling post: {title} for {publish_at}")
        else:
            print(f"Creating draft: {title}")

        # Parse markdown to Substack document format
        doc = parse_markdown_to_substack_doc(markdown_content)

        # Create post object
        post = Post(
            title=title,
            subtitle="",
            user_id=user_id,
            audience="everyone",
            write_comment_permissions="everyone",
        )

        # The draft_body needs to be a JSON string of the document structure
        draft_data = post.get_draft()
        draft_data["draft_body"] = json.dumps(doc)

        # Create draft on Substack
        draft = api.post_draft(draft_data)
        print(f"Draft response: {draft}")
        draft_id = draft.get("id") if isinstance(draft, dict) else None
        print(f"Draft ID: {draft_id}")
        result = {
            "status": "success",
            "paper_id": paper_id,
            "title": title,
            "draft_id": draft_id,
            "message": f"✅ Draft created successfully: {title}",
        }
        print(result["message"])

        # Schedule the draft if publish_at is provided
        if publish_at and draft_id:
            schedule_result = schedule_draft(draft_id, publish_at)
            result["scheduled"] = schedule_result["status"] == "success"
            if schedule_result["status"] == "success":
                result["message"] = (
                    f"✅ Draft created and scheduled for {publish_at}: {title}"
                )
            else:
                result["message"] = (
                    f"⚠️  Draft created but scheduling failed: {schedule_result.get('error', 'Unknown error')}"
                )

        return result

    except Exception as e:
        result = {
            "status": "error",
            "paper_id": paper_id,
            "error": str(e),
            "message": f"❌ Failed to create draft: {e}",
        }
        print(result["message"])
        return result


def post_all_papers(
    papers_date_folder: str,
    schedule_start_time: str = None,
    hours_between_posts: int = 24,
) -> list:
    """
    Post all markdown files from a date folder to Substack as drafts or scheduled posts.

    Args:
        papers_date_folder: Path to the folder containing paper markdown files
        schedule_start_time: Optional ISO 8601 datetime string to start scheduling (e.g., "2026-03-27T14:30:00Z")
                            If None, creates drafts. If provided, schedules posts at intervals.
        hours_between_posts: Hours to wait between each scheduled post (default: 24)

    Returns:
        List of results for each posted paper
    """
    from datetime import datetime, timedelta

    if not os.path.exists(papers_date_folder):
        print(f"❌ Folder not found: {papers_date_folder}")
        return []

    results = []
    markdown_files = []

    # Find all markdown summary files
    for root, dirs, files in os.walk(papers_date_folder):
        for file in files:
            if file.endswith("_summary.md"):
                markdown_files.append(os.path.join(root, file))

    if not markdown_files:
        print(f"⚠️  No markdown files found in {papers_date_folder}")
        return []

    print(f"\n--- POSTING {len(markdown_files)} PAPERS TO SUBSTACK ---")

    # Parse start time if provided
    current_publish_time = None
    if schedule_start_time:
        try:
            current_publish_time = datetime.fromisoformat(
                schedule_start_time.replace("Z", "+00:00")
            )
            print(f"📅 Scheduling posts starting at {current_publish_time}")
        except ValueError:
            print(
                f"⚠️  Invalid datetime format: {schedule_start_time}. Creating drafts instead."
            )

    for idx, markdown_path in enumerate(markdown_files):
        # Extract paper_id from filename
        filename = os.path.basename(markdown_path)
        paper_id = filename.replace("_summary.md", "")

        # Read markdown content
        with open(markdown_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        # Calculate publish time for this post
        publish_at = None
        if current_publish_time:
            publish_at = current_publish_time.isoformat()
            # Move to next scheduled time for next post
            current_publish_time += timedelta(hours=hours_between_posts)

        # Post to Substack
        result = post_to_substack(
            markdown_content, paper_id=paper_id, publish_at=publish_at
        )
        results.append(result)
        # break

    # Print summary
    successful = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "error")

    print("\n--- POSTING SUMMARY ---")
    print(f"✅ Successful: {successful}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")

    return results
