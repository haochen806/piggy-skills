#!/usr/bin/env python3
"""
DarkInterview HTML Extractor
Parses Next.js App Router RSC (React Server Components) payloads
from darkinterview.com HTML files and outputs structured JSON.

Usage:
    python3 extract.py                    # Process all files, output to stdout
    python3 extract.py --output out.json  # Write to file
    python3 extract.py --company openai   # Filter by company
    python3 extract.py --stats            # Print summary statistics
"""

import re
import json
import glob
import sys
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def extract_rsc_chunks(html_content: str) -> list[str]:
    """Extract all RSC payload chunks from self.__next_f.push([1,"..."]) blocks."""
    pattern = r'self\.__next_f\.push\(\[1,"(.*?)"\]\)'
    raw_matches = re.findall(pattern, html_content, re.DOTALL)
    chunks = []
    for raw in raw_matches:
        try:
            unescaped = raw.encode().decode('unicode_escape', errors='replace')
        except Exception:
            unescaped = raw
        chunks.append(unescaped)
    return chunks


def extract_questions_from_chunks(chunks: list[str]) -> tuple[str, str, list[dict], dict]:
    """
    Extract questions data from RSC chunks.

    Returns:
        (company_id, company_hash, questions_list, metadata_dict)
    """
    company_id = ""
    company_hash = ""
    questions = []
    metadata = {}

    for chunk in chunks:
        # Extract questions JSON array from the component props
        if '"questions":[{' in chunk:
            q_start = chunk.find('"questions":[')
            if q_start >= 0:
                bracket_start = chunk.index('[', q_start)
                depth = 0
                end_idx = bracket_start
                for end_idx in range(bracket_start, len(chunk)):
                    if chunk[end_idx] == '[':
                        depth += 1
                    elif chunk[end_idx] == ']':
                        depth -= 1
                    if depth == 0:
                        break
                q_json = chunk[bracket_start:end_idx + 1]
                try:
                    questions = json.loads(q_json)
                except json.JSONDecodeError:
                    pass

            # Extract company ID
            cid_match = re.search(r'"companyId":"(\w+)"', chunk)
            if cid_match:
                company_id = cid_match.group(1)

            # Extract company hash
            ch_match = re.search(r'"companyHash":"(\w+)"', chunk)
            if ch_match:
                company_hash = ch_match.group(1)

            # Extract subscription info
            has_sub = '"hasActiveSubscription":true' in chunk
            metadata['has_active_subscription'] = has_sub

            # Extract user info
            email_match = re.search(r'"userEmail":"([^"]+)"', chunk)
            if email_match:
                metadata['user_email'] = email_match.group(1)

        # Extract schema.org ItemList (has URLs)
        if '"@type":"ItemList"' in chunk:
            try:
                item_list = json.loads(chunk)
                metadata['schema_item_list'] = item_list
            except json.JSONDecodeError:
                pass

        # Extract page metadata (title, description)
        if '"metadata"' in chunk and '"title"' in chunk:
            title_match = re.search(r'"children":"([^"]*Interview Questions[^"]*)"', chunk)
            if title_match:
                metadata['page_title'] = title_match.group(1)

            desc_match = re.search(r'"description","content":"([^"]*)"', chunk)
            if desc_match:
                metadata['page_description'] = desc_match.group(1)

        # Extract last updated date
        updated_match = re.search(r'Updated \& Verified: ","([^"]+)"', chunk)
        if updated_match:
            metadata['last_updated'] = updated_match.group(1)

        # Extract total question count from badge
        count_match = re.search(r'\[(\d+)," active questions"\]', chunk)
        if count_match:
            metadata['active_question_count'] = int(count_match.group(1))

    return company_id, company_hash, questions, metadata


def extract_interview_data(chunks: list[str]) -> dict:
    """Extract data from interview landing pages."""
    data = {}

    for chunk in chunks:
        # Extract page metadata
        title_match = re.search(r'"children":"([^"]* Interview Questions[^"]*)"', chunk)
        if title_match and 'page_title' not in data:
            data['page_title'] = title_match.group(1)

        # Extract collection link
        col_match = re.search(r'/collections/(\w+)', chunk)
        if col_match:
            data['collection_hash'] = col_match.group(1)

        # Extract FAQ questions
        if 'FAQPage' in chunk or 'mainEntity' in chunk:
            faq_questions = re.findall(r'"name":"(.*?)"', chunk)
            # Filter to just the FAQ questions (skip schema names)
            faq_qs = [q for q in faq_questions if '?' in q]
            if faq_qs:
                data['faq_questions'] = faq_qs

        # Extract schema.org structured data
        if '"@type":"WebPage"' in chunk:
            try:
                schema = json.loads(chunk)
                data['schema_org'] = schema
            except json.JSONDecodeError:
                pass

    return data


def process_collection_file(filepath: str) -> dict:
    """Process a collection HTML file and return structured data."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    chunks = extract_rsc_chunks(content)
    company_id, company_hash, questions, metadata = extract_questions_from_chunks(chunks)

    # Build question URLs from schema.org ItemList if available
    url_map = {}
    if 'schema_item_list' in metadata:
        for item in metadata['schema_item_list'].get('itemListElement', []):
            name = item.get('name', '')
            url = item.get('url', '')
            url_map[name] = url

    # Enrich questions with URLs
    processed_questions = []
    for q in questions:
        question = {
            'id': q.get('id', ''),
            'title': q.get('title', ''),
            'category': q.get('category', ''),
            'order_index': q.get('order_index', 0),
            'is_free': q.get('is_free', False),
            'mask_title': q.get('mask_title', False),
            'archived': q.get('archived', False),
            'roles': q.get('roles', ''),
            'tags': q.get('tags', ''),
            'leetcode_slug': q.get('leetcode_slug'),
            'editor_type': q.get('editor_type'),
            'company_id': q.get('company_id', company_id),
        }

        # Add URL from schema.org data
        title = q.get('title', '')
        if title in url_map:
            question['url'] = url_map[title]
        elif company_hash and q.get('id'):
            question['url'] = f"https://darkinterview.com/collections/{company_hash}/questions/{q['id']}"

        processed_questions.append(question)

    return {
        'source_file': Path(filepath).name,
        'company_id': company_id,
        'company_hash': company_hash,
        'total_questions': len(processed_questions),
        'active_questions': len([q for q in processed_questions if not q['archived']]),
        'free_questions': len([q for q in processed_questions if q['is_free']]),
        'paid_questions': len([q for q in processed_questions if not q['is_free']]),
        'last_updated': metadata.get('last_updated', ''),
        'page_title': metadata.get('page_title', ''),
        'page_description': metadata.get('page_description', ''),
        'categories': sorted(set(q['category'] for q in processed_questions if q['category'])),
        'questions': processed_questions,
    }


def process_interview_file(filepath: str) -> dict:
    """Process an interview landing page HTML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    chunks = extract_rsc_chunks(content)
    data = extract_interview_data(chunks)

    # Extract company name from filename
    fname = Path(filepath).stem
    company = fname.replace('interview-', '')

    return {
        'source_file': Path(filepath).name,
        'company': company,
        'page_title': data.get('page_title', ''),
        'collection_hash': data.get('collection_hash', ''),
        'faq_questions': data.get('faq_questions', []),
    }


def main():
    parser = argparse.ArgumentParser(description='Extract DarkInterview problem data from HTML files')
    parser.add_argument('--dir', default=str(SCRIPT_DIR), help='Directory containing HTML files')
    parser.add_argument('--output', '-o', help='Output JSON file path (default: stdout)')
    parser.add_argument('--company', '-c', help='Filter by company ID (e.g., openai, anthropic)')
    parser.add_argument('--stats', '-s', action='store_true', help='Print summary statistics')
    parser.add_argument('--priority', action='store_true',
                        help='Only show priority companies: OpenAI, Anthropic, xAI, Netflix, Google')
    args = parser.parse_args()

    html_dir = args.dir

    # Process collection files
    collections = []
    for filepath in sorted(glob.glob(f'{html_dir}/collection-*.html')):
        result = process_collection_file(filepath)
        collections.append(result)

    # Process interview files
    interviews = []
    for filepath in sorted(glob.glob(f'{html_dir}/interview-*.html')):
        result = process_interview_file(filepath)
        interviews.append(result)

    # Filter by company if requested
    priority_companies = {'openai', 'anthropic', 'xai', 'netflix', 'google'}

    if args.company:
        collections = [c for c in collections if c['company_id'] == args.company]
        interviews = [i for i in interviews if i['company'] == args.company]
    elif args.priority:
        collections = [c for c in collections if c['company_id'] in priority_companies]
        interviews = [i for i in interviews if i['company'] in priority_companies]

    output = {
        'extraction_date': '2026-03-15',
        'source': 'darkinterview.com',
        'total_collections': len(collections),
        'total_interviews': len(interviews),
        'total_questions': sum(c['total_questions'] for c in collections),
        'company_to_collection_hash': {c['company_id']: c['company_hash'] for c in collections},
        'collections': collections,
        'interviews': interviews,
    }

    if args.stats:
        print("=" * 70)
        print("DarkInterview Extraction Summary")
        print("=" * 70)
        print(f"Total collection pages: {len(collections)}")
        print(f"Total interview pages:  {len(interviews)}")
        print(f"Total questions:        {output['total_questions']}")
        print()

        print("Company Breakdown:")
        print(f"{'Company':<15} {'Total':>6} {'Active':>7} {'Free':>5} {'Paid':>5} {'Categories'}")
        print("-" * 70)
        for c in sorted(collections, key=lambda x: x['total_questions'], reverse=True):
            marker = " *" if c['company_id'] in priority_companies else ""
            cats = ', '.join(c['categories'])
            print(f"{c['company_id']:<15} {c['total_questions']:>6} {c['active_questions']:>7} "
                  f"{c['free_questions']:>5} {c['paid_questions']:>5} {cats}{marker}")

        print()
        print("* = Priority company (OpenAI, Anthropic, xAI, Netflix, Google)")
        print()

        # Category breakdown
        all_cats = {}
        for c in collections:
            for q in c['questions']:
                cat = q['category']
                if cat not in all_cats:
                    all_cats[cat] = 0
                all_cats[cat] += 1

        print("Category Breakdown (all companies):")
        for cat, count in sorted(all_cats.items(), key=lambda x: -x[1]):
            print(f"  {cat:<25} {count:>4} questions")

        print()

        # High frequency tags
        hf_count = sum(1 for c in collections for q in c['questions']
                       if q.get('tags') and 'High Frequency' in q['tags'])
        new_count = sum(1 for c in collections for q in c['questions']
                        if q.get('tags') and 'New' in q['tags'])
        lc_count = sum(1 for c in collections for q in c['questions']
                       if q.get('leetcode_slug'))

        print(f"High Frequency tagged: {hf_count}")
        print(f"New tagged:            {new_count}")
        print(f"With LeetCode slug:    {lc_count}")
        print()

        # Masking analysis
        masked = sum(1 for c in collections for q in c['questions'] if q.get('mask_title'))
        unmasked = sum(1 for c in collections for q in c['questions'] if not q.get('mask_title'))
        print(f"mask_title=true:  {masked} (title hidden for non-subscribers)")
        print(f"mask_title=false: {unmasked} (title always visible)")

        return

    # Output JSON
    json_str = json.dumps(output, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(json_str)
        print(f"Written to {args.output}", file=sys.stderr)
        print(f"Total: {output['total_questions']} questions across {len(collections)} companies",
              file=sys.stderr)
    else:
        print(json_str)


if __name__ == '__main__':
    main()
