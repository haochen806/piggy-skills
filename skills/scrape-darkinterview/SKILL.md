---
name: scrape-darkinterview
description: Scrape all interview problems from darkinterview.com using curl + Python extraction. Use when asked to "scrape darkinterview", "refresh interview problems", or "update interview questions". Requires user to provide session cookie from browser DevTools.
allowed-tools: Bash, Read, Write, mcp__nanoclaw__send_message
---

# Scrape DarkInterview → Individual Problem Files

Fetch all interview problems from darkinterview.com and save as individual markdown files with a clean index.

## IMPORTANT: Why Not agent-browser?

darkinterview.com blocks headless Chromium (Google OAuth fails, magic link tokens get consumed by the user's browser). The **only working approach** is curl with session cookies exported from the user's real browser.

## Output Location

All output goes to `/workspace/group/darkinterview/`:
- `problems.md` — clean index linking to individual files
- `problems/` — one `.md` file per problem (e.g., `ant-c-001.md`)
- `plans.md` — study plans

## MANDATORY Output Format

Every problem file MUST follow this exact format (no exceptions):

```markdown
# {ID}: {Title}

- **Role**: {roles}
- **Tags**: {tags}
- **Difficulty**: {difficulty}
- **Source**: [{label}]({url})

**Problem:**

{full problem content here}
```

**Rules:**
- Filename: `{id}.md` all **lowercase** (e.g., `coi-c-001.md`, not `COI-C-001.md`)
- Title line includes the ID prefix: `# COI-C-001: Crypto Order System`
- Metadata uses `- **Key**: Value` format (dash-bullet, bold key, colon)
- Do NOT include copyright notices (`© 2026 Fluey AI`)
- Do NOT duplicate the title in the body
- Remove any `$L` obfuscated lines from the content
- The `**Problem:**` separator MUST appear before the problem body

**Company codes (all 10):**

| Company | Code | Hash |
|---------|------|------|
| anthropic | ANT | a3b8c1d5 |
| coinbase | COI | c4b7e2m9 |
| databricks | DAT | q2w5e8r1 |
| netflix | NFL | n3f6x9k2 |
| openai | OAI | x7k9m2p4 |
| perplexity | PER | j6h3k9n2 |
| rippling | RIP | r8p2l5g7 |
| snowflake | SNO | s9w2f6l4 |
| stripe | STR | t4y7u1i8 |
| xai | XAI | m5n8v3x1 |

**Category codes:**

| Category | Code |
|----------|------|
| Behavioral | BH |
| Coding | C |
| Data Modeling | DM |
| Debug | DBG |
| Integration | INT |
| ML System Design | ML |
| OA | OA |
| Problem Solving | PS |
| System Design | SD |
| System Programming | SYS |

## Scripts Location

Two Python extraction scripts are bundled with this skill:
- `/home/node/.claude/skills/scrape-darkinterview/extract-collections.py`
- `/home/node/.claude/skills/scrape-darkinterview/extract-questions.py`

Copy them to a working directory before use:
```bash
WORK_DIR=/tmp/darkinterview
mkdir -p "$WORK_DIR/questions"
cp /home/node/.claude/skills/scrape-darkinterview/extract-collections.py "$WORK_DIR/"
cp /home/node/.claude/skills/scrape-darkinterview/extract-questions.py "$WORK_DIR/"
```

---

## Step 1: Get Session Cookie from User

Ask the user to provide their `__Secure-authjs.session-token` cookie value:

```
mcp__nanoclaw__send_message(message: "To scrape darkinterview.com, I need your session cookie.\n\n1. Open https://darkinterview.com/collections in your browser\n2. Open DevTools (F12) → Application tab → Cookies\n3. Find `__Secure-authjs.session-token`\n4. Copy and paste the full value here\n\nThis is a NextAuth.js JWT token from your paid account.")
```

Wait for the user to reply with the cookie value.

Store it:
```bash
WORK_DIR=/tmp/darkinterview
COOKIE="__Secure-authjs.session-token=USER_PROVIDED_VALUE_HERE"
```

## Step 2: Identify Target Companies

darkinterview.com organizes problems by company collections. Each company has a unique hash in its URL.

Known company hashes (as of March 2026):
```
anthropic  → a3b8c1d5
openai     → b7d4e2f1
xai        → c5a9d3e7
netflix    → d2f6b8a4
```

If these change, discover them by fetching the main collections page:
```bash
curl -s -b "$COOKIE" "https://darkinterview.com/collections" -o "$WORK_DIR/collections-index.html"
# Look for /collections/{hash} links in the RSC payload
grep -oP '/collections/[a-f0-9]+' "$WORK_DIR/collections-index.html" | sort -u
```

## Step 3: Fetch Collection Pages (Question Metadata)

For each company, fetch the collection page which contains the question list with metadata (titles, IDs, categories, roles, tags):

```bash
# Priority companies
declare -A COMPANIES=(
  ["anthropic"]="a3b8c1d5"
  ["openai"]="b7d4e2f1"
  ["xai"]="c5a9d3e7"
  ["netflix"]="d2f6b8a4"
)

for company in "${!COMPANIES[@]}"; do
  hash="${COMPANIES[$company]}"
  echo "Fetching $company collection ($hash)..."
  curl -s -b "$COOKIE" \
    "https://darkinterview.com/collections/$hash" \
    -o "$WORK_DIR/collection-$company.html"
  sleep 1
done
```

## Step 4: Extract Question Metadata

Run the collections extractor to get structured JSON with all question IDs and metadata:

```bash
cd "$WORK_DIR"
python3 extract-collections.py --dir "$WORK_DIR" --priority -o "$WORK_DIR/priority-problems.json"
```

This outputs `priority-problems.json` with:
- Question IDs (UUIDs)
- Titles, categories, roles, tags
- Free/paid status
- Company collection hashes (for building question URLs)

Verify the output:
```bash
python3 extract-collections.py --dir "$WORK_DIR" --priority --stats
```

## Step 5: Fetch Individual Question Pages

Each question has a detail page at:
`https://darkinterview.com/collections/{company_hash}/questions/{question_id}`

Batch fetch all questions (with rate limiting):

```bash
# Parse question URLs from priority-problems.json
python3 -c "
import json
with open('$WORK_DIR/priority-problems.json') as f:
    data = json.load(f)
for coll in data['collections']:
    company_hash = coll['company_hash']
    company_id = coll['company_id']
    for q in coll['questions']:
        qid = q['id']
        print(f'{company_id}\t{company_hash}\t{qid}')
" > "$WORK_DIR/question-urls.tsv"

# Fetch in batches of 10 with 1s delay between batches
COUNT=0
while IFS=$'\t' read -r company hash qid; do
  OUT="$WORK_DIR/questions/${company}-${qid}.html"
  if [ ! -f "$OUT" ]; then
    curl -s -b "$COOKIE" \
      "https://darkinterview.com/collections/$hash/questions/$qid" \
      -o "$OUT"
    COUNT=$((COUNT + 1))
    if [ $((COUNT % 10)) -eq 0 ]; then
      echo "Fetched $COUNT questions..."
      sleep 1
    fi
  fi
done < "$WORK_DIR/question-urls.tsv"
echo "Total fetched: $COUNT"
```

Send progress update:
```
mcp__nanoclaw__send_message(message: "Fetched {COUNT} question pages. Now extracting content...")
```

## Step 6: Extract Question Content

Run the question extractor to parse RSC payloads into structured JSON:

```bash
cd "$WORK_DIR"
python3 extract-questions.py
```

This reads all HTML files in `questions/` and outputs `questions-full.json` with:
- Full problem markdown (problem statement, hints, solutions, follow-ups)
- Structured sections
- Metadata merged from priority-problems.json

## Step 7: Generate Individual Problem Files

Convert the JSON into individual markdown files with a naming convention:

```bash
OUTPUT_DIR="/workspace/group/darkinterview/problems"
mkdir -p "$OUTPUT_DIR"

python3 -c "
import json, re, os

with open('$WORK_DIR/questions-full.json') as f:
    data = json.load(f)

# Company short codes
COMPANY_CODES = {
    'anthropic': 'ANT',
    'coinbase': 'COI',
    'databricks': 'DAT',
    'netflix': 'NFL',
    'openai': 'OAI',
    'perplexity': 'PER',
    'rippling': 'RIP',
    'snowflake': 'SNO',
    'stripe': 'STR',
    'xai': 'XAI',
}

# Category short codes
CATEGORY_CODES = {
    'Behavioral': 'BH',
    'Coding': 'C',
    'Data Modeling': 'DM',
    'Debug': 'DBG',
    'Integration': 'INT',
    'ML System Design': 'ML',
    'OA': 'OA',
    'Problem Solving': 'PS',
    'System Design': 'SD',
    'System Programming': 'SYS',
}

# Group by company + category and assign IDs
groups = {}
for q in data['questions']:
    company = q['company']
    category = q['category']
    key = (company, category)
    if key not in groups:
        groups[key] = []
    groups[key].append(q)

# Sort each group by order_index
for key in groups:
    groups[key].sort(key=lambda x: x['order_index'])

# Generate files
index_entries = {}
for (company, category), questions in sorted(groups.items()):
    cc = COMPANY_CODES.get(company, company.upper()[:3])
    cat = CATEGORY_CODES.get(category, category[0].upper())

    for i, q in enumerate(questions, 1):
        problem_id = f'{cc}-{cat}-{i:03d}'
        filename = f'{problem_id.lower()}.md'

        # Build markdown
        md_lines = [f'# {problem_id}: {q[\"title\"]}', '']
        md_lines.append(f'- **Role**: {q.get(\"roles\", \"Software Engineer\")}')
        if q.get('tags'):
            md_lines.append(f'- **Tags**: {q[\"tags\"]}')
        md_lines.append(f'- **Difficulty**: Medium')
        if q.get('url'):
            is_free = q.get('is_free', False)
            label = 'Free' if is_free else 'DarkInterview'
            md_lines.append(f'- **Source**: [{label}]({q[\"url\"]})')
        md_lines.append('')
        md_lines.append('**Problem:**')
        md_lines.append('')
        md_lines.append(q.get('full_markdown', '(content not available)'))

        filepath = os.path.join('$OUTPUT_DIR', filename)
        with open(filepath, 'w') as f:
            f.write('\n'.join(md_lines))

        # Track for index
        if company not in index_entries:
            index_entries[company] = {}
        if category not in index_entries[company]:
            index_entries[company][category] = []
        index_entries[company][category].append({
            'id': problem_id,
            'filename': filename,
            'title': q['title'],
            'roles': q.get('roles', ''),
            'tags': q.get('tags', ''),
            'is_free': q.get('is_free', False)
        })

# Generate index
with open('/workspace/group/darkinterview/problems.md', 'w') as f:
    total = sum(len(qs) for cats in index_entries.values() for qs in cats.values())
    f.write(f'# Dark Interview Problems\n\n')
    f.write(f'> Scraped from darkinterview.com on $(date +%Y-%m-%d)\n')
    f.write(f'> Total: {total} problems across {len(index_entries)} companies\n')
    f.write(f'> Each problem is a separate file in \`problems/\` for easy context management\n\n')

    for company in sorted(index_entries.keys()):
        f.write(f'## {company.title()}\n\n')
        for category in sorted(index_entries[company].keys()):
            f.write(f'### {category}\n\n')
            for entry in index_entries[company][category]:
                tags = ''
                parts = []
                if entry['roles']:
                    parts.append(entry['roles'])
                if entry['tags']:
                    parts.append(entry['tags'])
                if entry['is_free']:
                    parts.append('Free')
                if parts:
                    tags = f' *({', '.join(parts)})*'
                f.write(f'- [{entry[\"id\"]}: {entry[\"title\"]}](problems/{entry[\"filename\"]}){tags}\n')
            f.write('\n')

print(f'Generated {total} problem files in $OUTPUT_DIR')
print(f'Updated index at /workspace/group/darkinterview/problems.md')
"
```

## Step 8: Verify and Report

```bash
echo "=== Problem files ==="
ls /workspace/group/darkinterview/problems/ | wc -l
echo "=== Index preview ==="
head -30 /workspace/group/darkinterview/problems.md
```

```
mcp__nanoclaw__send_message(message: "Done! Scraped and organized {N} problems from darkinterview.com.\n\nFiles:\n• problems.md — clean index\n• problems/ — {N} individual files\n• plans.md — study plans\n\nAll in your darkinterview/ folder.")
```

---

## How the RSC Extraction Works

darkinterview.com is a Next.js App Router site. Data is embedded in React Server Components (RSC) payloads, NOT in traditional `__NEXT_DATA__` JSON.

### Data Format

RSC payloads are embedded in HTML as:
```javascript
self.__next_f.push([1,"...escaped RSC payload..."])
```

Each payload contains line entries like:
```
3a:["$","div",null,{"children":["$","h2",null,{"children":"Problem Title"}]}]
```

### Collection Pages

Collection pages contain a JSON array of question objects:
```json
{"questions":[{"id":"uuid","title":"...","category":"Coding","roles":"Software Engineer","tags":"High Frequency","is_free":false,...}]}
```

The `extract-collections.py` script:
1. Regex-extracts all `self.__next_f.push` blocks
2. Unicode-unescapes the payloads
3. Finds the `"questions":[{` JSON array via bracket-depth counting
4. Extracts company metadata (companyId, companyHash)

### Question Detail Pages

Individual question pages embed the full problem content as nested RSC nodes:
```json
["$","h2",null,{"children":"Follow-up: Multithreaded Implementation"}]
["$","p",null,{"children":"Implement a concurrent version..."}]
["$","code",null,{"className":"hljs language-python","children":"def crawl(...):\n    ..."}]
```

The `extract-questions.py` script:
1. Parses all RSC payload blocks
2. Splits entries by hex ID prefix (e.g., `3a:`)
3. Recursively extracts structured content from RSC nodes
4. Converts to markdown (headings, paragraphs, code blocks, lists)
5. Filters out watermark spans (`content-watermark` class)
6. Merges with metadata from `priority-problems.json`

### Content Obfuscation (Paid Problems)

Paid problems have portions of their solution code obfuscated with `$L` prefix variables:
```javascript
$L6e
$L6f { task, resolve, reject } = $L70.$L71.$L72();
```

The problem statement and requirements are always fully visible. Only solution code may be partially obfuscated. This is DRM — the extracted markdown preserves whatever is visible.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **403 on question pages** | Cookie expired. Ask user for fresh `__Secure-authjs.session-token` |
| **Empty HTML files** | Check if file contains "Sign in" — means auth failed |
| **Missing questions in JSON** | Some companies may have changed their collection hash. Re-discover hashes from collections index page |
| **Script import errors** | Scripts need Python 3.8+. Install if missing: `apt-get install -y python3` |
| **Rate limiting** | Increase sleep between batches from 1s to 2-3s |
| **New companies added** | Fetch `/collections` index, extract new hashes from `/collections/{hash}` links |

## Refreshing Problems

To update existing problems (e.g., new questions added):

1. Re-run Steps 3-7 with fresh cookie
2. The scripts are idempotent — existing HTML files in `questions/` won't be re-fetched (skip logic in Step 5)
3. To force re-fetch everything: `rm -rf $WORK_DIR/questions/*.html`
4. After extraction, the index and individual files are fully regenerated
