# EZCollegeApp Market Agent

An LLM-powered Reddit marketing agent that monitors college application subreddits, replies to relevant posts with genuine advice that naturally mentions EZCollegeApp, and creates on-demand promotional posts.

Replies are **grounded in a 300-entry college-admissions knowledge base** via semantic retrieval (RAG), so the advice is accurate and specific. The product mention is a single passive, feature-specific aside placed after the real advice — never a pitch, never a URL.

---

## Table of Contents

- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Configuration](#configuration)
- [Knowledge Base & RAG](#knowledge-base--rag)
- [JSON Files Reference](#json-files-reference)
- [Prompt Files Reference](#prompt-files-reference)
- [Running the Agent](#running-the-agent)
- [Testing Guide](#testing-guide)
- [Going Live](#going-live)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Orchestrator                          │
│   Reads config, wires all agents together, exposes CLI       │
└──────────────────────────────┬──────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                                          │
┌─────────▼──────────┐                   ┌──────────▼──────────┐
│   Monitor Agent    │                   │    Post Agent        │
│                    │                   │  (on-demand only)    │
│ 1. Scan subreddits │                   │                      │
│ 2. Keyword filter  │                   │ 1. Generate post     │
│ 3. LLM relevance   │                   │ 2. Parse title/body  │
│    classifier      │                   │ 3. Submit or dry-run │
└─────────┬──────────┘                   └─────────────────────┘
          │
┌─────────▼──────────┐
│    Reply Agent     │
│                    │
│ 1. Generate reply  │
│ 2. Self-critique   │
│    (LLM review)    │
│ 3. Submit or       │
│    dry-run/queue   │
└─────────┬──────────┘
          │
┌─────────▼──────────────────────────────────────────────────┐
│                       Shared Tools                          │
│  LLMClient (OpenAI / Gemini)  │  RedditTool (PRAW)         │
│  MemoryTool (JSON state)      │  PromptLoader (YAML / MD)  │
│  RAGTool (semantic retrieval over the knowledge base)      │
└────────────────────────────────────────────────────────────┘
```

### Agent Flow (Monitor Mode)

```
scheduler.py / main.py monitor
        │
        ▼
Orchestrator.run_monitor_cycle()
        │
        ▼
MonitorAgent.scan(subreddits)
  ├── For each post:
  │     ├── memory.has_replied(id)?  → skip if yes
  │     ├── keyword_match(post)?     → skip if no keywords found
  │     └── LLM relevance check      → skip if not relevant
  └── Yield relevant posts
        │
        ▼
ReplyAgent.reply(post)
  ├── Check daily reply limit
  ├── RAGTool.retrieve(post)   → top-k knowledge-base entries (fail-open → none)
  ├── Load prompts (product_context.md, brand_voice.md, advertorial_strategy.md,
  │     subreddit guide) + inject retrieved knowledge
  ├── LLM call → generate reply (grounded advice + passive feature-specific mention)
  ├── LLM self-critique → approve or reject (also rejects URLs / overt pitches)
  └── If approved:
        ├── RedditTool.reply_to_post()  [live / dry-run / review]
        └── MemoryTool.mark_replied() + log_reply()
```

### Post Agent Flow (On-Demand)

```
main.py post --subreddit ApplyingToCollege --format story
        │
        ▼
PostAgent.post(subreddit, format, context)
  ├── Check daily post limit
  ├── Load prompts
  ├── LLM call → generate TITLE + BODY
  ├── Parse output
  └── RedditTool.make_post()  [live / dry-run / review]
```

---

## Project Structure

```
ezcommon_market_agent/
│
├── agents/                         # Agent logic
│   ├── orchestrator.py             # Wires config + all agents; CLI entry-point
│   ├── monitor_agent.py            # Subreddit scanner + relevance classifier
│   ├── reply_agent.py              # Reply generator with self-critique
│   └── post_agent.py               # On-demand promotional post generator
│
├── tools/                          # Shared low-level tools
│   ├── llm_client.py               # OpenAI / Gemini chat + OpenAI embeddings
│   ├── reddit_tool.py              # PRAW wrapper (dry-run, review-mode aware)
│   ├── memory_tool.py              # Read/write state.json and reply_log.json
│   ├── rag_tool.py                 # Semantic retrieval over the knowledge base
│   └── prompt_loader.py            # Loads YAML prompt templates and .md files
│
├── knowledge_base/                 # RAG knowledge base + cached embeddings
│   ├── general-all-merged.json     # 300 sourced college-admissions entries
│   ├── advertorial-agent-knowledge-base.md  # Full product/feature reference
│   └── embeddings_cache.npz        # Cached vectors (committed; auto-rebuilds on change)
│
├── prompts/                        # Prompt templates and context files
│   ├── product_context.md          # What EZCollegeApp is (injected into every prompt)
│   ├── brand_voice.md              # Tone and style rules
│   ├── advertorial_strategy.md     # Soft-ad strategy: pain→feature map, varied framing
│   ├── subreddit_ApplyingToCollege.md  # Per-subreddit personality guide
│   ├── reply_prompt.yaml           # System + user prompt for reply generation
│   └── post_prompt.yaml            # System + user prompt for post generation
│
├── memory/                         # Persistent operational state (gitignore this)
│   ├── state.json                  # Replied post IDs, daily counters
│   └── reply_log.json              # Full history of all generated replies/posts
│
├── review_queue/
│   └── review_queue.json           # Pending items in review mode
│
├── config/
│   └── settings.yaml               # Subreddits, keywords, rate limits, LLM config
│
├── tests/
│   ├── conftest.py                 # Shared pytest fixtures and mock LLM factories
│   ├── fixtures/
│   │   ├── post_relevant.json      # Sample relevant Reddit post
│   │   ├── post_irrelevant.json    # Sample off-topic post
│   │   └── post_already_replied.json  # Sample post already in memory
│   ├── test_dry_run.py             # Layer 1: dry-run mode tests
│   ├── test_fixtures.py            # Layer 2: unit tests using static fixtures
│   └── test_reddit_sandbox.py      # Layer 3: live Reddit sandbox tests
│
├── main.py                         # CLI entry-point
├── scheduler.py                    # APScheduler recurring monitor loop
├── requirements.txt
└── .env.example                    # Template for environment variables
```

---

## Setup

### Prerequisites

- **Python 3.10+** (the code uses `X | None` type syntax).
- An **OpenAI API key** (required — used for RAG embeddings even if you chat via Gemini).
- A **Reddit account + app credentials** (only needed to actually post; reads and dry-run work without them).

### 1. Install dependencies

A virtual environment is recommended:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Dependencies (`requirements.txt`): `openai`, `google-generativeai`, `praw` (Reddit writes),
`requests` (Reddit reads), `numpy` (RAG similarity), `pyyaml`, `python-dotenv`, `apscheduler`
(scheduler), `pytest` + `pytest-mock` (tests).

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```env
# LLM Provider (pick one for chat)
OPENAI_API_KEY=sk-...        # REQUIRED — also used for RAG embeddings even if LLM_PROVIDER=gemini
GEMINI_API_KEY=...
LLM_PROVIDER=openai          # openai | gemini (controls chat only; embeddings are always OpenAI)

# Reddit API (create an app at https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
REDDIT_USER_AGENT=ezcommon_market_agent/1.0 by u/your_username

# Agent behavior
DRY_RUN=true                 # Start with true. Set false only when ready to go live.
REVIEW_MODE=false            # Set true to queue replies for human review instead of posting
```

### 3. Configure subreddits and keywords

Edit `config/settings.yaml` to adjust target subreddits, keywords, rate limits, and LLM model choices.

---

## Configuration

`config/settings.yaml` controls all runtime behavior:

```yaml
subreddits:                  # Subreddits to scan
  - ApplyingToCollege
  - college
  - SAT

keywords:                    # Pre-filter: post must contain at least one
  - college application
  - common app
  - personal statement

rate_limits:
  max_replies_per_day: 10    # Hard cap on replies per day
  max_posts_per_day: 2       # Hard cap on posts per day
  min_delay_between_replies_seconds: 300  # Pause between successive replies

llm:
  provider: openai           # Overridden by LLM_PROVIDER env var
  openai_model: gpt-4o
  gemini_model: gemini-1.5-pro
  openai_embed_model: text-embedding-3-small  # RAG always embeds via OpenAI

rag:
  enabled: true              # Set false to reply without knowledge-base grounding
  top_k: 3                   # Knowledge-base entries injected per reply
  kb_file: knowledge_base/general-all-merged.json
  cache_file: knowledge_base/embeddings_cache.npz

reddit:
  post_limit: 25             # How many posts to scan per subreddit per run
  scan_interval_seconds: 3600  # How often the scheduler triggers (1 hour)
```

---

## Knowledge Base & RAG

Replies are grounded in a knowledge base so the advice is accurate and specific rather than
generic model output.

### How it works

1. **`knowledge_base/general-all-merged.json`** holds 300 expert, sourced college-admissions
   entries (title + content + tags).
2. On first run, `RAGTool` embeds every entry with OpenAI `text-embedding-3-small` and caches the
   vectors to **`knowledge_base/embeddings_cache.npz`**.
3. For each candidate post, `RAGTool.retrieve()` embeds the post, ranks all entries by cosine
   similarity, and injects the **top `top_k`** entries into the reply prompt as grounding.
4. The model writes the advice from that grounded context, then adds one passive, feature-specific
   EZCollegeApp mention (per `prompts/advertorial_strategy.md`).

### The embedding cache

- The cache is **committed to git**, so every clone/account reuses the same vectors with **no
  re-embedding cost** on first run.
- It is keyed by a fingerprint of `(knowledge base file bytes + embedding model)`. If you edit
  `general-all-merged.json` or change the embed model, the cache **auto-rebuilds** on the next run
  (and you should commit the regenerated `.npz`).
- To force a rebuild, delete `knowledge_base/embeddings_cache.npz` and run any monitor cycle.

### Fail-open behavior

If embeddings are unavailable (e.g. missing `OPENAI_API_KEY`) or retrieval errors, the agent logs
a warning and replies **ungrounded** rather than crashing. Set `rag.enabled: false` in
`settings.yaml` to disable retrieval entirely.

> **Note:** RAG embeddings always use OpenAI, even when `LLM_PROVIDER=gemini`. An `OPENAI_API_KEY`
> is required for grounded replies regardless of the chat provider.

---

## JSON Files Reference

### `memory/state.json`

Tracks which posts have been replied to and enforces daily rate limits. Reset automatically each day.

```json
{
  "replied_post_ids": ["abc123", "xyz789"],
  "daily_reply_count": 3,
  "daily_post_count": 0,
  "last_reset_date": "2026-03-08"
}
```

| Field | Type | Description |
|---|---|---|
| `replied_post_ids` | `string[]` | Reddit post IDs already replied to (deduplication) |
| `daily_reply_count` | `int` | Replies submitted today (resets at midnight) |
| `daily_post_count` | `int` | Posts submitted today (resets at midnight) |
| `last_reset_date` | `string` | ISO date of last counter reset |

**Do not edit this file manually unless you want to re-process a post or reset a counter.**

---

### `memory/reply_log.json`

Append-only history of every reply and post the agent has generated. Useful for auditing and quality review.

```json
[
  {
    "post_id": "abc123",
    "post_title": "How do I write a Common App essay?",
    "subreddit": "ApplyingToCollege",
    "reply": "Great question! Start with a specific memory...",
    "timestamp": "2026-03-08T14:22:01+00:00"
  },
  {
    "type": "post",
    "subreddit": "ApplyingToCollege",
    "title": "How I finally nailed my Common App essay",
    "body": "...",
    "url": "https://reddit.com/r/ApplyingToCollege/...",
    "timestamp": "2026-03-08T16:00:00+00:00"
  }
]
```

---

### `review_queue/review_queue.json`

Used when `REVIEW_MODE=true`. The agent writes items here instead of posting to Reddit. You review and approve/reject manually, then run the submission script.

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "action": "reply",
    "post_id": "abc123",
    "text": "Great question! ...",
    "timestamp": "2026-03-08T14:22:01+00:00",
    "status": "pending"
  }
]
```

| Field | Values | Description |
|---|---|---|
| `action` | `reply` \| `post` | Whether this is a reply to an existing post or a new post |
| `status` | `pending` \| `approved` \| `rejected` | Set manually after review |
| `text` | string | Reply body (for `action: reply`) |
| `title` / `body` | string | Post title and body (for `action: post`) |

**Workflow**: Run agent with `REVIEW_MODE=true` → inspect this file → change `status` to `approved` or `rejected` → run submission.

---

## Prompt Files Reference

All `.md` files in `prompts/` are **injected directly into LLM prompts at runtime** — edit them to tune the agent's voice and behavior without changing any code.

| File | Purpose |
|---|---|
| `product_context.md` | Full description of EZCollegeApp (features, value prop, URL). Injected into every reply and post prompt. |
| `brand_voice.md` | Tone rules: what to do and not do. Defines the "feel" of every reply. |
| `advertorial_strategy.md` | Soft-ad strategy injected into reply prompts: pain→feature map, passive framing, the no-URL rule, and the varied-phrasing menu (so mentions don't read as templated). |
| `subreddit_ApplyingToCollege.md` | Community-specific guide for r/ApplyingToCollege. Add more files named `subreddit_<name>.md` for additional subreddits. |
| `reply_prompt.yaml` | YAML with `system_prompt` and `user_prompt` templates for reply generation. |
| `post_prompt.yaml` | YAML with `system_prompt` and `user_prompt` templates for post generation. |

---

## Running the Agent

### One-shot monitor cycle (scan + reply)

```bash
python main.py monitor
```

### Create an on-demand post

```bash
# Story post (personal experience angle)
python main.py post --subreddit ApplyingToCollege --format story

# Tips post ("things I wish I knew")
python main.py post --subreddit college --format tips

# Question-style post with a custom angle
python main.py post --subreddit ApplyingToCollege --format question \
  --context "students struggling with the activities section"
```

### Start the recurring scheduler (runs every hour)

```bash
python scheduler.py
```

---

## Testing Guide

### Layer 1 — Dry-Run Mode (no API keys needed)

Tests that `DRY_RUN=true` correctly blocks all Reddit writes. The LLM pipeline is fully exercised using mock LLM responses — no real API calls.

```bash
pytest tests/test_dry_run.py -v
```

**What is tested:**
- `RedditTool` never builds a PRAW client in dry-run mode
- `reply_to_post()` and `make_post()` print output and return without submitting
- `ReplyAgent` calls the LLM pipeline, respects the daily reply cap, and marks posts as replied in memory
- `PostAgent` generates and parses a post, respects the daily post cap

---

### Layer 2 — Static Fixture Tests (no API keys needed)

Feeds saved Reddit post snapshots from `tests/fixtures/` directly to agents. No network calls at all.

```bash
pytest tests/test_fixtures.py -v
```

**What is tested:**
- `MemoryTool` deduplication, daily counters, and reply log
- `MonitorAgent` keyword pre-filter correctly passes/blocks posts
- `MonitorAgent` LLM relevance classifier returns correct results and handles malformed JSON safely
- `ReplyAgent` self-critique approves good replies and rejects spammy ones
- `ReplyAgent` does not submit or log a reply that was rejected
- `PostAgent` TITLE/BODY output parser handles valid and invalid LLM output
- `LLMClient` raises proper errors for unsupported providers and missing API keys

**Adding your own fixture posts:**

Save a Reddit post as JSON in `tests/fixtures/` using this format:

```json
{
  "id": "reddit_post_id",
  "title": "Post title here",
  "body": "Post body here",
  "subreddit": "ApplyingToCollege",
  "url": "https://reddit.com/r/ApplyingToCollege/comments/..."
}
```

---

### Layer 3 — Reddit Sandbox (requires real credentials)

Runs the full pipeline against a real Reddit account, targeting `r/test` (or your own private subreddit). Tests are **automatically skipped** when credentials are not present — safe for CI.

**Required environment variables:**

```bash
export REDDIT_CLIENT_ID=...
export REDDIT_CLIENT_SECRET=...
export REDDIT_USERNAME=...
export REDDIT_PASSWORD=...
export OPENAI_API_KEY=...        # or GEMINI_API_KEY
```

**Optionally, target your own private subreddit:**

```bash
export SANDBOX_SUBREDDIT=ezcollegeapp_test   # default is "test"
```

**Run:**

```bash
pytest tests/test_reddit_sandbox.py -v -s
```

**What is tested:**
- Reddit authentication succeeds with provided credentials
- `scan_subreddit()` returns posts with correct fields
- A real reply is submitted to a test post and verified in comments (test post is auto-deleted after)
- A real post is submitted and verified via URL (auto-deleted after)
- `REVIEW_MODE=true` writes to `review_queue.json` instead of posting

---

### Run all tests at once

```bash
# Layer 1 + Layer 2 only (no credentials needed — always safe)
pytest tests/test_dry_run.py tests/test_fixtures.py -v

# All three layers (Layer 3 skips automatically without credentials)
pytest tests/ -v
```

---

## Going Live

Follow this progression to safely move from testing to real Reddit activity:

### Step 1 — Tune reply quality

Run with `DRY_RUN=true` and watch the printed output. Edit `prompts/brand_voice.md` and `prompts/product_context.md` until the generated replies feel natural.

```bash
DRY_RUN=true python main.py monitor
```

### Step 2 — Use review mode for human approval

Switch to `REVIEW_MODE=true`. The agent scans real Reddit and generates real replies, but writes them to `review_queue/review_queue.json` instead of posting.

```bash
REVIEW_MODE=true DRY_RUN=false python main.py monitor
```

Inspect the file, then manually change `"status": "pending"` to `"approved"` or `"rejected"` for each entry.

### Step 3 — Sandbox subreddit

Test the full write path against `r/test` or your own private subreddit with `DRY_RUN=false` and `REVIEW_MODE=false`. Confirm auth, submission, and rate limiting all work.

```bash
SANDBOX_SUBREDDIT=your_private_sub pytest tests/test_reddit_sandbox.py -v -s
```

### Step 4 — Go live

Set `DRY_RUN=false` and `REVIEW_MODE=false` in your `.env`. Start with a low `max_replies_per_day` (e.g., 3) and monitor manually for the first few days.

```bash
DRY_RUN=false REVIEW_MODE=false python scheduler.py
```

> **Note:** Reddit's spam detection is sensitive to repetitive behavior. Keep replies varied, maintain delays between submissions, and never post the same text twice. The agent enforces these via `rate_limits` in `settings.yaml` and the deduplication in `state.json`.
