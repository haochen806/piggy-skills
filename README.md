# Piggy Skills

Custom skills, agents, and commands for the Piggy AI assistant (Claude Code / nanoclaw).

## Skills

| Skill | Description |
|-------|-------------|
| **agent-browser** | Browse the web — open pages, click, fill forms, take screenshots, extract data |
| **gan-style-harness** | GAN-inspired Generator-Evaluator harness for building apps autonomously (based on [Anthropic's March 2026 paper](https://www.anthropic.com/engineering/harness-design-long-running-apps)) |
| **interview-helper** | Interview coaching with real problems from darkinterview.com — Socratic coaching, rubric feedback, mock interviews |
| **maintain-darkinterview** | Maintain and deploy the Dark Interview site at acehouse.poker/darkinterview/ |
| **paper-to-xhs** | Research AI papers from X/Twitter and publish formatted 小红书 posts |
| **scrape-darkinterview** | Scrape interview problems from darkinterview.com with Python extraction |
| **search-xhs** | Search and browse 小红书 content for travel, food, activities, product research |
| **tools-to-xhs** | Research AI tools/products and publish formatted 小红书 posts |

## Agents (GAN Harness)

| Agent | Role |
|-------|------|
| **gan-planner** | Product Manager — expands brief into full product spec |
| **gan-generator** | Developer — builds the app, reads evaluator feedback, iterates |
| **gan-evaluator** | QA Engineer — tests live app via Playwright, scores against rubric |

## Commands

| Command | Description |
|---------|-------------|
| **gan-build** | Full three-agent GAN harness build |
| **gan-design** | Two-agent frontend design mode |

## Installation

Copy to your Claude Code config directory:

```bash
cp -r skills/* ~/.claude/skills/
cp -r agents/* ~/.claude/agents/
cp -r commands/* ~/.claude/commands/
cp -r scripts/* ~/.claude/scripts/
```
