"""
Convert markdown research paper summaries to beautiful HTML for Substack publishing.
"""

import os
import re


def markdown_to_html(markdown_text: str) -> str:
    """
    Convert markdown to beautiful HTML suitable for Substack.
    Preserves all content while adding styling.
    """
    html = markdown_text

    # Convert headers
    html = re.sub(
        r"^# (.*?)$",
        r'<h1 style="font-size: 2.5em; font-weight: 700; margin: 1.5em 0 0.5em 0; color: #1a1a1a; line-height: 1.2;">\1</h1>',
        html,
        flags=re.MULTILINE,
    )
    html = re.sub(
        r"^## (.*?)$",
        r'<h2 style="font-size: 1.8em; font-weight: 600; margin: 1.5em 0 0.75em 0; color: #2a2a2a; line-height: 1.3;">\1</h2>',
        html,
        flags=re.MULTILINE,
    )
    html = re.sub(
        r"^### (.*?)$",
        r'<h3 style="font-size: 1.3em; font-weight: 600; margin: 1.2em 0 0.6em 0; color: #3a3a3a;">\1</h3>',
        html,
        flags=re.MULTILINE,
    )

    # Convert bold text
    html = re.sub(
        r"\*\*(.*?)\*\*",
        r'<strong style="font-weight: 600; color: #1a1a1a;">\1</strong>',
        html,
    )

    # Convert italic text
    html = re.sub(
        r"\*(.*?)\*", r'<em style="font-style: italic; color: #555;">\1</em>', html
    )

    # Convert links
    html = re.sub(
        r"\[(.*?)\]\((.*?)\)",
        r'<a href="\2" style="color: #0066cc; text-decoration: none; border-bottom: 1px solid #0066cc;">\1</a>',
        html,
    )

    # Convert bullet points and nested lists
    lines = html.split("\n")
    processed_lines = []
    in_list = False
    in_nested_list = False

    for line in lines:
        # Detect list items
        if re.match(r"^\s*\+\s", line):
            # Nested bullet (indented with +)
            if not in_nested_list:
                processed_lines.append(
                    '<ul style="margin: 0.5em 0 0.5em 2em; padding: 0;">'
                )
                in_nested_list = True
            content = re.sub(r"^\s*\+\s", "", line)
            processed_lines.append(
                f'<li style="margin: 0.3em 0; line-height: 1.6; color: #333;">{content}</li>'
            )
        elif re.match(r"^\s*\*\s", line):
            # Main bullet point
            if in_nested_list:
                processed_lines.append("</ul>")
                in_nested_list = False
            if not in_list:
                processed_lines.append(
                    '<ul style="margin: 0.8em 0; padding: 0; list-style-position: outside;">'
                )
                in_list = True
            content = re.sub(r"^\s*\*\s", "", line)
            processed_lines.append(
                f'<li style="margin: 0.5em 0; line-height: 1.7; color: #333; margin-left: 1.5em;">{content}</li>'
            )
        else:
            # Close lists if we hit non-list content
            if in_nested_list:
                processed_lines.append("</ul>")
                in_nested_list = False
            if in_list and line.strip():
                processed_lines.append("</ul>")
                in_list = False

            # Add paragraph tags for non-empty lines
            if line.strip() and not line.startswith("<"):
                processed_lines.append(
                    f'<p style="margin: 1em 0; line-height: 1.8; color: #333; font-size: 1em;">{line}</p>'
                )
            elif line.strip():
                processed_lines.append(line)

    # Close any open lists
    if in_nested_list:
        processed_lines.append("</ul>")
    if in_list:
        processed_lines.append("</ul>")

    html = "\n".join(processed_lines)

    # Wrap everything in a container with Substack-friendly styling
    html = f"""<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 2em 1.5em; color: #333; line-height: 1.6;">
{html}
</div>"""

    return html


def convert_summary_to_html(markdown_path: str, output_path: str = None) -> str:
    """
    Convert a markdown summary file to HTML.

    Args:
        markdown_path: Path to the markdown file
        output_path: Optional path to save HTML file. If None, saves to same directory with .html extension

    Returns:
        The generated HTML string
    """
    # Read markdown file
    with open(markdown_path, "r", encoding="utf-8") as f:
        markdown_text = f.read()

    # Convert to HTML
    html = markdown_to_html(markdown_text)

    # Determine output path
    if output_path is None:
        output_path = markdown_path.replace(".md", ".html")

    # Save HTML file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Converted to HTML: {output_path}")
    return html


def convert_all_summaries_to_html(papers_dir: str = "papers") -> list:
    """
    Convert all markdown summaries in the papers directory to HTML.

    Args:
        papers_dir: Root directory containing paper folders

    Returns:
        List of paths to generated HTML files
    """
    html_files = []

    # Find all summary.md files
    for root, dirs, files in os.walk(papers_dir):
        if "summary.md" in files:
            markdown_path = os.path.join(root, "summary.md")
            html_path = os.path.join(root, "summary.html")

            try:
                convert_summary_to_html(markdown_path, html_path)
                html_files.append(html_path)
            except Exception as e:
                print(f"❌ Error converting {markdown_path}: {e}")

    return html_files


def create_substack_post_html(
    html_content: str, title: str = "AI Research Digest"
) -> str:
    """
    Wrap HTML content in a complete Substack-ready post template.

    Args:
        html_content: The HTML content to wrap
        title: Post title

    Returns:
        Complete HTML post ready for Substack
    """
    post_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 700px;
            margin: 0 auto;
            background-color: white;
            padding: 3em 2em;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            font-size: 2.5em;
            font-weight: 700;
            margin: 1.5em 0 0.5em 0;
            color: #1a1a1a;
            line-height: 1.2;
        }}
        h2 {{
            font-size: 1.8em;
            font-weight: 600;
            margin: 1.5em 0 0.75em 0;
            color: #2a2a2a;
            line-height: 1.3;
        }}
        h3 {{
            font-size: 1.3em;
            font-weight: 600;
            margin: 1.2em 0 0.6em 0;
            color: #3a3a3a;
        }}
        p {{
            margin: 1em 0;
            line-height: 1.8;
            color: #333;
            font-size: 1em;
        }}
        strong {{
            font-weight: 600;
            color: #1a1a1a;
        }}
        em {{
            font-style: italic;
            color: #555;
        }}
        a {{
            color: #0066cc;
            text-decoration: none;
            border-bottom: 1px solid #0066cc;
        }}
        a:hover {{
            color: #0052a3;
        }}
        ul {{
            margin: 0.8em 0;
            padding: 0;
            list-style-position: outside;
        }}
        li {{
            margin: 0.5em 0;
            line-height: 1.7;
            color: #333;
            margin-left: 1.5em;
        }}
        ul ul {{
            margin: 0.5em 0 0.5em 2em;
            padding: 0;
        }}
        ul ul li {{
            margin: 0.3em 0;
            margin-left: 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        {html_content}
    </div>
</body>
</html>"""
    return post_html
