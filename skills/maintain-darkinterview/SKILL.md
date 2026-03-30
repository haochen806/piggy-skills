---
name: maintain-darkinterview
description: Maintain and publish the Dark Interview site at acehouse.poker/darkinterview/ — add/update/remove interview problems, update the SPA, and deploy to Cloudflare Pages. Use when asked to "update darkinterview", "add problems", "publish darkinterview", "deploy darkinterview", or any maintenance of the interview problem collection.
allowed-tools: Bash, Read, Write, Edit, WebFetch, mcp__nanoclaw__send_message
---

# Maintain & Publish Dark Interview (acehouse.poker/darkinterview/)

A static SPA serving 244+ interview problems across 10 companies. Files live in the poker-game repo at `apps/web/public/darkinterview/` and deploy via Cloudflare Pages.

## End-to-End Workflow

```
scrape-darkinterview skill        this skill (maintain-darkinterview)
         │                                    │
    Scrape problems ──→ /workspace/group/darkinterview/
                                              │
                              ┌───────────────┼───────────────┐
                              ▼               ▼               ▼
                         Clone repo     Copy files in     Build & Deploy
                         (poker-game)   Update index      (wrangler)
```

---

## Phase 1: Clone the Poker-Game Repo

```bash
REPO_DIR="/workspace/group/poker-game"
if [ ! -d "$REPO_DIR/.git" ]; then
  git clone --depth 1 https://github.com/haochen806/poker-game.git "$REPO_DIR"
else
  cd "$REPO_DIR" && git pull origin main
fi
```

The darkinterview files live at: `$REPO_DIR/apps/web/public/darkinterview/`

## Phase 2: Integrate Scraped Problems

If the `scrape-darkinterview` skill has already run and produced files in `/workspace/group/darkinterview/`, copy them into the repo:

```bash
REPO_DI="$REPO_DIR/apps/web/public/darkinterview"

# Copy problem files
cp /workspace/group/darkinterview/problems/*.md "$REPO_DI/problems/"

# Copy updated index
cp /workspace/group/darkinterview/problems.md "$REPO_DI/problems.md"
```

Then update `index.html` counts and company pages (see sections below).

## Phase 3: Update index.html

The SPA has two JS arrays that **MUST** stay in sync with the actual files.

### COMPANIES array (~line 194)

Each entry: `{ slug: '{slug}', name: '{Name}', count: {N} }`

```javascript
const COMPANIES = [
  { slug: 'anthropic', name: 'Anthropic', count: 20 },
  { slug: 'coinbase', name: 'Coinbase', count: 16 },
  { slug: 'databricks', name: 'Databricks', count: 26 },
  { slug: 'netflix', name: 'Netflix', count: 35 },
  { slug: 'openai', name: 'OpenAI', count: 33 },
  { slug: 'perplexity', name: 'Perplexity', count: 13 },
  { slug: 'rippling', name: 'Rippling', count: 11 },
  { slug: 'snowflake', name: 'Snowflake', count: 51 },
  { slug: 'stripe', name: 'Stripe', count: 24 },
  { slug: 'xai', name: 'xAI', count: 15 },
];
```

### PREFIX_MAP (~line 207)

Maps slug to 3-letter file prefix:

```javascript
const PREFIX_MAP = {
  anthropic: 'ant', coinbase: 'coi', databricks: 'dat', netflix: 'nfl',
  openai: 'oai', perplexity: 'per', rippling: 'rip', snowflake: 'sno',
  stripe: 'str', xai: 'xai',
};
```

### Total count in showIndex() (~line 273)

```javascript
html += '<p style="color:#888;margin-bottom:24px">244 problems across 10 companies</p>';
```

### Auto-update counts from actual files:

```bash
REPO_DI="$REPO_DIR/apps/web/public/darkinterview"
echo "=== Problem counts per company ==="
for slug in anthropic coinbase databricks netflix openai perplexity rippling snowflake stripe xai; do
  prefix=$(echo "$slug" | head -c3)
  # Map special prefixes
  case "$slug" in
    netflix) prefix="nfl" ;;
    openai) prefix="oai" ;;
    perplexity) prefix="per" ;;
    rippling) prefix="rip" ;;
    snowflake) prefix="sno" ;;
    stripe) prefix="str" ;;
    *) prefix=$(echo "$slug" | head -c3) ;;
  esac
  count=$(ls "$REPO_DI/problems/${prefix}-"*.md 2>/dev/null | wc -l)
  echo "$slug: $count"
done
total=$(ls "$REPO_DI/problems/"*.md 2>/dev/null | wc -l)
echo "TOTAL: $total"
```

Use these counts to update the COMPANIES array and total in index.html.

---

## Phase 4: Build & Deploy to Cloudflare Pages

### Prerequisites

The container needs these env vars (set via nanoclaw .env):
- `CLOUDFLARE_API_TOKEN` — Cloudflare API token with Pages edit permission
- `CLOUDFLARE_ACCOUNT_ID` — Cloudflare account ID

### Build the frontend

```bash
cd "$REPO_DIR/apps/web"
npm install
npm run build
```

The `dist/` directory will contain everything including `darkinterview/`.

### Deploy

```bash
cd "$REPO_DIR/apps/web"
npx wrangler pages deploy dist --project-name=acehouse --branch=main
```

### Verify deployment

```bash
# Check the site is live
curl -s -o /dev/null -w "%{http_code}" https://acehouse.poker/darkinterview/
# Should return 200
```

Send result:
```
mcp__nanoclaw__send_message(message: "Published to acehouse.poker/darkinterview/\n\nUpdated: {N} problems across {M} companies\nDeploy status: ✓")
```

---

## Codebase Reference

### Company Codes & Hashes

| Company    | Code | Slug       | Hash     |
|------------|------|------------|----------|
| Anthropic  | ANT  | anthropic  | a3b8c1d5 |
| Coinbase   | COI  | coinbase   | c4b7e2m9 |
| Databricks | DAT  | databricks | q2w5e8r1 |
| Netflix    | NFL  | netflix    | n3f6x9k2 |
| OpenAI     | OAI  | openai     | x7k9m2p4 |
| Perplexity | PER  | perplexity | j6h3k9n2 |
| Rippling   | RIP  | rippling   | r8p2l5g7 |
| Snowflake  | SNO  | snowflake  | s9w2f6l4 |
| Stripe     | STR  | stripe     | t4y7u1i8 |
| xAI        | XAI  | xai        | m5n8v3x1 |

### Category Codes

| Category           | Code |
|--------------------|------|
| Behavioral         | BH   |
| Coding             | C    |
| Data Modeling      | DM   |
| Debug              | DBG  |
| Integration        | INT  |
| ML System Design   | ML   |
| OA                 | OA   |
| Problem Solving    | PS   |
| System Design      | SD   |
| System Programming | SYS  |

### Problem File Format

Filename: `{code}-{cat}-{num}.md` all lowercase (e.g., `ant-c-001.md`)

```markdown
# {Title}

**Company:** {Company Name}
**Category:** {Category}
**Free:** {Yes|No}
**URL:** https://darkinterview.com/collections/{hash}/questions/{uuid}

---

# {Title}

## {Section}

{Content}
```

### problems.md Index Format

```markdown
# Dark Interview Problems

> Scraped from darkinterview.com on {date}
> Total: {N} problems across {M} companies

- [Company](#company) (count)

---

## {Company Name}

### {Category}

- [{CODE-CAT-NUM}: {Title}](problems/{code-cat-num}.md) *({Role}, {Tags})*
```

### Company File Format (companies/{slug}.md)

```markdown
# {Company} Interview Problems

**Total:** {N} problems

## Standard Questions

### {Problem Title}

- **Category:** {Category} Problems
- **Roles:** {SWE, MLE, etc.}
- **File:** `{code-cat-num}.md`
```

---

## Common Tasks

### Adding a New Company

1. Create `companies/{slug}.md`
2. Create problem files in `problems/`
3. Add `## {Company}` section to `problems.md`
4. Add to COMPANIES array in `index.html` (alphabetical)
5. Add to PREFIX_MAP in `index.html`
6. Update totals
7. Deploy

### Removing a Problem

1. Delete `problems/{id}.md`
2. Remove entry from `problems.md`
3. Update `companies/{slug}.md` and decrement total
4. Decrement count in COMPANIES array
5. Deploy

---

## Verification Checklist

Before deploying, verify:

- [ ] All files in `problems.md` exist in `problems/`
- [ ] COMPANIES counts match actual file counts
- [ ] Total in `showIndex()` matches sum of COMPANIES counts
- [ ] PREFIX_MAP has all companies
- [ ] Company files have correct totals
- [ ] Filenames are all lowercase
- [ ] No duplicate problem IDs
- [ ] `CLOUDFLARE_API_TOKEN` is set (check with `echo $CLOUDFLARE_API_TOKEN | head -c8`)

Verify links:
```bash
grep -oP 'problems/[\w-]+\.md' "$REPO_DI/problems.md" | while read f; do
  [ -f "$REPO_DI/$f" ] || echo "MISSING: $f"
done
```
