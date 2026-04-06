---
name: tools-to-xhs
description: Research a recent AI tool, product launch, or open-source project and create + publish a formatted XHS post. Use when the user asks to "post an AI tool to XHS", "write about a new AI tool", or "find trending AI tools and share".
allowed-tools: WebSearch, WebFetch, Bash, Read, Write, mcp__nanoclaw__xhs_post
---

# AI Tool/News → XHS Pipeline

You find a recent, trending AI tool, product, or open-source project, write a Chinese XHS-style long article, and publish it.

## ⚠️ WEEKEND-ONLY PUBLISHING RULE

**Only publish to 小红书 on weekends (Saturday & Sunday).** Posting on weekdays risks getting flagged by XHS. If it's a weekday:
1. Still research and prepare the post (images + text)
2. Save everything to the posts/ folder as usual
3. Do NOT call `mcp__nanoclaw__xhs_post` — tell the user the post is ready and will be published on the weekend
4. If the user explicitly insists on publishing now, warn them about the risk first

## CRITICAL: Post Directory

All post files MUST go in `/workspace/project/posts/{FOLDER}/`. Do NOT use `/workspace/group/posts/` or any relative `posts/` path — the XHS publishing tool only reads from `/workspace/project/posts/`.

## Step 1: Find a Trending AI Tool or News

Search for recent AI tools, product launches, open-source releases, or significant updates (≤2 weeks old):

```
WebSearch: new AI tool launch 2026 March
WebSearch: open source AI agent framework release site:github.com 2026
WebSearch: AI product launch site:x.com OR twitter.com 2026
WebSearch: "claude code" OR "cursor" OR "windsurf" new feature 2026
WebSearch: AI developer tools trending this week
```

Good sources:
- X/Twitter: @AnthropicAI, @OpenAI, @GoogleDeepMind, @huggingface, @LangChainAI, @llaboratories
- GitHub trending, Hacker News, Product Hunt
- Official blogs: Anthropic, OpenAI, Google DeepMind, Meta AI

Look for:
- New tool/product launches (Claude Code features, Cursor updates, new frameworks)
- Open-source project releases (NanoClaw, OpenClaw, IronClaw, agent frameworks)
- Major feature updates to existing tools
- Surprising or practical AI applications
- Developer experience improvements

Pick the most interesting/impactful item.

## Step 2: Research the Tool

Gather details:

```
WebFetch: {official website or GitHub repo}
WebFetch: {blog post or announcement}
WebFetch: {demo or documentation page}
```

Extract:
- **Tool name** and version
- **Creator/company** and their background
- **What it does** — core functionality in 1-2 sentences
- **Key features** — 3-5 standout capabilities
- **How it differs** from alternatives
- **Pricing/availability** (open-source? free? paid?)
- **Screenshots or diagrams** from the official site

## Step 3: Create Post Folder and Download Images

Folder name format: `{YYYY-MM-DD}-{keyword}` where keyword is a short slug (lowercase, hyphens).

```bash
DATE=$(date +%Y-%m-%d)
KEYWORD="claude-remote"   # short slug: e.g. "openclaw", "cursor-update", "agent-sdk"
FOLDER="${DATE}-${KEYWORD}"
mkdir -p /workspace/project/posts/$FOLDER
```

Download **2-4 images** — screenshots, UI demos, architecture diagrams from official sources.

```bash
curl -L -o /workspace/project/posts/$FOLDER/img1.png "{screenshot_url}"
curl -L -o /workspace/project/posts/$FOLDER/img2.png "{feature_demo_url}"

# IMPORTANT: Verify files are actual images, not HTML error pages
file /workspace/project/posts/$FOLDER/img*.png
# Each must say "PNG image data" or "JPEG image data"
# If any says "HTML document", the download failed — try alternative URLs
```

Good image choices:
- `img1.png` — Product UI screenshot or logo + tagline
- `img2.png` — Key feature demo or workflow diagram
- `img3.png` — Comparison chart or architecture overview
- `img4.png` — Code example screenshot or results

## Step 4: Write the Post Content

Create `/workspace/project/posts/$FOLDER/text` following this structure:

```
{Chinese title with one emoji at end}

🛠️ Tool: {Tool Name} {version if applicable}
👤 By: {Creator/Company}
🔗 {website or GitHub URL}

🔍 What is it?

{2-3 paragraphs explaining:
1. What the tool IS and what problem it solves
2. Why it matters NOW — what changed or what's new
3. Who should care — target audience}

📌 {N} Features

（一）{Feature 1}
▪️ {detail}: {explanation}
▪️ {detail}: {explanation}
→ Why it matters: {practical impact}

（二）{Feature 2}
▪️ {detail}: {explanation}
▪️ {detail}: {explanation}

（三）{Feature 3}
▪️ {detail}: {explanation}
⚠️ {limitation or caveat if any}

🔄 vs alternatives

• vs {Alternative A}: {1-sentence comparison}
• vs {Alternative B}: {1-sentence comparison}
→ Best for: {specific use case where this tool wins}

💡 Most interesting detail

{1-2 paragraphs on the most surprising capability or design decision.
Explain WHY this matters and what it reveals about the direction of AI tooling.
Use bold **text** to highlight the core insight.}

🤖 My take

{1 paragraph: your honest opinion. Is this worth trying? Who benefits most?
What's the catch? Sound like a fellow developer sharing a genuine take.}

#ai #tool #{topic1} #{topic2} #Developer #人工智能 #开发工具 #开源
```

## Title Rules

- **First line** of the `text` file becomes the XHS title field (≤20 chars)
- **Use Chinese** — avoid mixing in English words unless the term has no natural Chinese equivalent (tool names like "Claude Code" are fine)
- Include one emoji at the end
- Examples: `Claude Code远程控制来了🔥` / `开源Agent框架新选择💡` / `AI编程工具大更新🚀`

## Content Rules

- Write entirely in **Simplified Chinese** (English tool names and technical terms are OK)
- Tool name, creator, and link must appear in the header
- **Explain what the tool does clearly** — don't assume readers know the category
- Use XHS-style emoji section headers
- Sub-bullets: use ▪️ for items, • for comparisons, → for conclusions, ⚠️ for caveats
- Be **specific** — include version numbers, dates, pricing
- End with **6-8 hashtags** mixing English and Chinese, each separated by a space

## Tag Spacing

Hashtags in the last line must have a space between each tag:
```
#ai #tool #ClaudeCode #Agent #Developer #人工智能 #开发工具 #开源
```

## Step 5: Publish to XHS

Call the MCP tool directly — do NOT write IPC files manually:

```
mcp__nanoclaw__xhs_post(postFolder: "{FOLDER}")
```

## Troubleshooting

- **Downloaded file is HTML, not an image**: the URL returned an error page. Try alternative URLs or take screenshots via agent-browser
- **No good screenshots available**: use `agent-browser open {url}` then `agent-browser screenshot` to capture your own
- **Post not publishing**: make sure files are in `/workspace/project/posts/` (NOT `/workspace/group/posts/`)
