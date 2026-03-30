#!/usr/bin/env python3
"""
Extract interview questions from darkinterview.com Next.js RSC HTML files.
Parses self.__next_f.push([1,"..."]) blocks to extract problem content.
Combines with metadata from priority-problems.json.
Outputs questions-full.json.
"""

import re
import json
import os
import sys
import argparse
from pathlib import Path

# Defaults — overridable via CLI args
DEFAULT_DIR = Path("/tmp/darkinterview")
QUESTIONS_DIR = DEFAULT_DIR / "questions"
PRIORITY_FILE = DEFAULT_DIR / "priority-problems.json"
OUTPUT_FILE = DEFAULT_DIR / "questions-full.json"


def decode_rsc_block(raw: str) -> str:
    """Decode a raw RSC payload string (with unicode escapes)."""
    try:
        return raw.encode('utf-8').decode('unicode_escape')
    except Exception:
        return raw


def extract_text_from_rsc_node(node) -> str:
    """Recursively extract plain text from an RSC JSON node."""
    if node is None or node == "$undefined":
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        # Check if it's a React element: ["$", "tag", key, props]
        if len(node) >= 4 and node[0] == "$":
            tag = node[1]
            props = node[3] if len(node) > 3 and isinstance(node[3], dict) else {}

            # Skip watermark spans
            if isinstance(props, dict):
                cn = props.get("className", "")
                if "content-watermark" in cn:
                    return ""

            children = props.get("children", "") if isinstance(props, dict) else ""
            text = extract_text_from_rsc_node(children)

            # Handle code blocks
            if tag and isinstance(tag, str):
                if tag == "code" and not props.get("className", ""):
                    return f"`{text}`"

            return text
        else:
            # It's a plain array of children
            parts = []
            for item in node:
                parts.append(extract_text_from_rsc_node(item))
            return "".join(parts)
    return str(node)


def extract_structured_content(node, depth=0) -> list:
    """
    Extract structured content from RSC nodes.
    Returns a list of (type, content) tuples.
    Types: h1, h2, h3, p, code_block, ul, ol, hr, task_list
    """
    results = []
    if node is None or node == "$undefined":
        return results
    if isinstance(node, str):
        stripped = node.strip()
        if stripped:
            results.append(("text", stripped))
        return results
    if isinstance(node, list):
        if len(node) >= 4 and node[0] == "$":
            tag = node[1]
            props = node[3] if len(node) > 3 and isinstance(node[3], dict) else {}

            if isinstance(props, dict):
                cn = props.get("className", "")
                if "content-watermark" in cn:
                    return results

            children = props.get("children", "") if isinstance(props, dict) else ""

            # Handle specific tags
            if tag == "h1":
                results.append(("h1", extract_text_from_rsc_node(children)))
            elif tag == "h2":
                results.append(("h2", extract_text_from_rsc_node(children)))
            elif tag == "h3":
                results.append(("h3", extract_text_from_rsc_node(children)))
            elif tag == "p":
                results.append(("p", extract_text_from_rsc_node(children)))
            elif tag == "hr":
                results.append(("hr", "---"))
            elif tag == "ul":
                items = extract_list_items(children)
                if isinstance(props, dict) and "contains-task-list" in props.get("className", ""):
                    results.append(("task_list", items))
                else:
                    results.append(("ul", items))
            elif tag == "ol":
                items = extract_list_items(children)
                results.append(("ol", items))
            elif tag == "code":
                cn = props.get("className", "") if isinstance(props, dict) else ""
                if "hljs" in cn or (isinstance(children, str) and "\n" in children):
                    # It's a code block
                    code_text = extract_text_from_rsc_node(children)
                    lang = ""
                    if "language-" in cn:
                        lang = cn.split("language-")[1].split(" ")[0].split("\"")[0]
                    results.append(("code_block", {"lang": lang, "code": code_text}))
                else:
                    results.append(("inline_code", extract_text_from_rsc_node(children)))
            elif tag and isinstance(tag, str) and tag.startswith("$L"):
                # Component wrapper - extract children
                results.extend(extract_structured_content(children, depth + 1))
            elif tag == "div":
                cn = props.get("className", "") if isinstance(props, dict) else ""
                if "mb-6" in cn:
                    # This is likely a difficulty/tag badge container rendered client-side, skip
                    pass
                else:
                    results.extend(extract_structured_content(children, depth + 1))
            elif tag == "strong":
                results.append(("strong", extract_text_from_rsc_node(children)))
            elif tag == "li":
                results.append(("li", extract_text_from_rsc_node(children)))
            elif tag == "input":
                pass  # checkbox in task list
            else:
                results.extend(extract_structured_content(children, depth + 1))
        else:
            # Plain array of children
            for item in node:
                results.extend(extract_structured_content(item, depth))
    return results


def extract_list_items(node) -> list:
    """Extract list items from a ul/ol children node."""
    items = []
    if isinstance(node, list):
        if len(node) >= 4 and node[0] == "$":
            tag = node[1]
            if tag == "li":
                props = node[3] if len(node) > 3 and isinstance(node[3], dict) else {}
                children = props.get("children", "") if isinstance(props, dict) else ""
                items.append(extract_text_from_rsc_node(children))
            else:
                # Recurse
                props = node[3] if len(node) > 3 and isinstance(node[3], dict) else {}
                children = props.get("children", "") if isinstance(props, dict) else ""
                items.extend(extract_list_items(children))
        else:
            for item in node:
                items.extend(extract_list_items(item))
    return items


def content_to_markdown(structured_content: list) -> str:
    """Convert structured content list to markdown string."""
    lines = []
    for item_type, content in structured_content:
        if item_type == "h1":
            lines.append(f"# {content}")
            lines.append("")
        elif item_type == "h2":
            lines.append(f"## {content}")
            lines.append("")
        elif item_type == "h3":
            lines.append(f"### {content}")
            lines.append("")
        elif item_type == "p":
            lines.append(content)
            lines.append("")
        elif item_type == "text":
            pass  # Skip loose text (usually newlines)
        elif item_type == "ul":
            for li in content:
                lines.append(f"- {li}")
            lines.append("")
        elif item_type == "ol":
            for i, li in enumerate(content, 1):
                lines.append(f"{i}. {li}")
            lines.append("")
        elif item_type == "task_list":
            for li in content:
                lines.append(f"- [ ] {li}")
            lines.append("")
        elif item_type == "code_block":
            lang = content.get("lang", "")
            code = content.get("code", "")
            lines.append(f"```{lang}")
            lines.append(code)
            lines.append("```")
            lines.append("")
        elif item_type == "hr":
            lines.append("---")
            lines.append("")
        elif item_type == "strong":
            lines.append(f"**{content}**")
            lines.append("")
        elif item_type == "li":
            lines.append(f"- {content}")
    return "\n".join(lines)


def parse_rsc_content_blocks(html_content: str) -> list:
    """
    Parse all RSC payload blocks from an HTML file.
    Returns decoded content strings.
    """
    pattern = r'self\.__next_f\.push\(\[1,"(.*?)"\]\)'
    matches = re.findall(pattern, html_content, re.DOTALL)
    decoded_blocks = []
    for m in matches:
        decoded = decode_rsc_block(m)
        decoded_blocks.append(decoded)
    return decoded_blocks


def find_content_blocks(blocks: list) -> list:
    """
    Find blocks that contain the actual question content (h1, h2, h3, p, etc.)
    These are the blocks with RSC line references like '37:[...]'
    """
    content_lines = []
    for block in blocks:
        # Each block may contain multiple RSC line entries like "37:[...]"
        # Parse them out
        lines = re.split(r'\n(?=[0-9a-f]+:)', block)
        for line in lines:
            content_lines.append(line)
    return content_lines


def parse_rsc_json_value(text: str):
    """Try to parse an RSC line value as JSON."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


def extract_question_content(html_path: str) -> dict:
    """
    Extract the full question content from an HTML file.
    Returns a dict with title, description_md, sections, etc.
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    blocks = parse_rsc_content_blocks(html_content)

    # Collect all RSC entries across all blocks
    all_entries = {}
    for block in blocks:
        # Split by RSC line references: hex_id:value
        entries = re.split(r'\n(?=[0-9a-f]+:)', block)
        for entry in entries:
            match = re.match(r'^([0-9a-f]+):(.*)', entry, re.DOTALL)
            if match:
                key = match.group(1)
                value_str = match.group(2)
                parsed = parse_rsc_json_value(value_str)
                if parsed is not None:
                    all_entries[key] = parsed

    # Now find the main content - look for h1 element
    title = ""
    all_content = []

    for key, value in sorted(all_entries.items(), key=lambda x: int(x[0], 16)):
        structured = extract_structured_content(value)
        if structured:
            all_content.extend(structured)
            # Find the title (h1)
            for item_type, content in structured:
                if item_type == "h1" and not title:
                    title = content

    # Convert to markdown
    full_markdown = content_to_markdown(all_content)

    # Extract sections from the structured content
    sections = {}
    current_section = "description"
    current_content = []

    for item_type, content in all_content:
        if item_type == "h2":
            if current_content:
                sections[current_section] = content_to_markdown(current_content)
            current_section = content.lower().strip()
            current_content = []
        else:
            current_content.append((item_type, content))

    if current_content:
        sections[current_section] = content_to_markdown(current_content)

    # Extract hints - look for h2/h3 with "hint" in name
    hints = []
    for section_name, section_content in sections.items():
        if "hint" in section_name.lower():
            hints.append(section_content.strip())

    # Extract follow-ups
    follow_ups = []
    for section_name, section_content in sections.items():
        if "follow" in section_name.lower() or "extension" in section_name.lower():
            follow_ups.append(section_content.strip())

    return {
        "title": title,
        "full_markdown": full_markdown,
        "sections": sections,
        "hints": hints,
        "follow_ups": follow_ups,
    }


def main():
    parser = argparse.ArgumentParser(description='Extract question content from darkinterview HTML files')
    parser.add_argument('--dir', default=str(DEFAULT_DIR), help='Working directory (default: /tmp/darkinterview)')
    args = parser.parse_args()

    work_dir = Path(args.dir)
    questions_dir = work_dir / "questions"
    priority_file = work_dir / "priority-problems.json"
    output_file = work_dir / "questions-full.json"

    # Load priority-problems metadata
    with open(priority_file, 'r') as f:
        priority_data = json.load(f)

    # Build a lookup from question ID to metadata
    question_meta = {}
    for coll in priority_data["collections"]:
        for q in coll["questions"]:
            question_meta[q["id"]] = q

    # Process all HTML files
    results = []
    html_files = sorted(questions_dir.glob("*.html"))
    print(f"Processing {len(html_files)} HTML files...")

    for i, html_file in enumerate(html_files):
        # Extract company and question ID from filename: company-uuid.html
        fname = html_file.stem
        parts = fname.split("-", 1)
        company = parts[0]
        question_id = parts[1] if len(parts) > 1 else fname

        print(f"  [{i+1}/{len(html_files)}] {fname}")

        # Get metadata
        meta = question_meta.get(question_id, {})

        # Extract content from HTML
        try:
            content = extract_question_content(str(html_file))
        except Exception as e:
            print(f"    ERROR: {e}")
            content = {
                "title": meta.get("title", fname),
                "full_markdown": "",
                "sections": {},
                "hints": [],
                "follow_ups": [],
            }

        # Combine metadata and content
        result = {
            "id": question_id,
            "company": company,
            "title": meta.get("title", content["title"]),
            "clean_title": content["title"],  # Title from the HTML h1
            "category": meta.get("category", "Unknown"),
            "order_index": meta.get("order_index", 999),
            "is_free": meta.get("is_free", False),
            "roles": meta.get("roles", ""),
            "tags": meta.get("tags", ""),
            "leetcode_slug": meta.get("leetcode_slug"),
            "url": meta.get("url", ""),
            "full_markdown": content["full_markdown"],
            "sections": content["sections"],
            "hints": content["hints"],
            "follow_ups": content["follow_ups"],
        }
        results.append(result)

    # Sort by company, then category, then order_index
    results.sort(key=lambda x: (x["company"], x["category"], x["order_index"]))

    # Output
    output = {
        "extraction_date": priority_data.get("extraction_date", "2026-03-15"),
        "source": "darkinterview.com",
        "total_questions": len(results),
        "questions": results,
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(results)} questions to {output_file}")

    # Print summary
    companies = {}
    for q in results:
        c = q["company"]
        if c not in companies:
            companies[c] = {}
        cat = q["category"]
        if cat not in companies[c]:
            companies[c][cat] = 0
        companies[c][cat] += 1

    print("\nSummary:")
    for company, cats in sorted(companies.items()):
        total = sum(cats.values())
        print(f"  {company}: {total} questions")
        for cat, count in sorted(cats.items()):
            print(f"    {cat}: {count}")


if __name__ == "__main__":
    main()
