# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BCTone (비씨톤) is a Slack AI assistant for the GrowFit 4-person dev team. It runs in Socket Mode, silently collects channel messages to classify progress/decisions, answers technical questions via @mention, summarizes GitHub activity, and posts automated daily/weekly reports.

The product it supports — GrowFit — is an AI-based learning platform with a 3-tier permission model (student, instructor, admin). Backend repo: `GF_for_CODEX` (FastAPI + SQLAlchemy + PostgreSQL). Frontend repo: `GF_Frontend` (React 19 + React Router 7).

## Commands

```bash
# Run the bot
python -m bctone.app

# Run all tests
pytest

# Run a single test file / single test
pytest tests/test_handlers.py
pytest tests/test_handlers.py::test_handle_mention_calls_chat

# Install dependencies
pip install -r requirements.txt
```

## Architecture

**Entry point:** `bctone/app.py` — creates the Slack Bolt app, registers event handlers, starts APScheduler, and launches Socket Mode.

**Event flow:**
- `message` events → `handlers/message.py` — silently classifies messages via LLM (PROGRESS / DECISION / TODO / NONE) and saves non-trivial ones to `bctone.memories`
- `app_mention` events → `handlers/mention.py` — retrieves thread conversation history, calls LLM chat with context, saves both user/assistant turns to `bctone.conversations`
- `/bctone` slash command → `handlers/command.py` — routes to `summarizer` (team progress or GitHub summaries)

**LLM layer (`services/llm.py`):**
- Uses the Anthropic Python SDK. Client is lazily initialized (reads `ANTHROPIC_API_KEY` from env).
- Auto-routes between Sonnet (simple) and Opus (complex) via an escalation classifier.
- Exposes: `classify_message`, `chat`, `summarize`, `parse_todo`, `should_escalate`.

**Data layer:**
- PostgreSQL with a `bctone` schema. Three tables: `memories`, `conversations`, `reports`.
- Raw SQL via `psycopg2` — no ORM. All queries are in `services/memory.py` and `scheduler/daily_report.py`.
- Connection factory: `db.get_connection()`. Schema bootstrap: `db.init_schema()`.

**Scheduler (`scheduler/daily_report.py`):**
- APScheduler `BackgroundScheduler` with `Asia/Seoul` timezone.
- Weekday 9 AM: daily report. Monday 9:30 AM: weekly report. Midnight: expired memory cleanup.
- Reports are posted to `#bot-log` channel and archived in `bctone.reports`.

**Config (`config.py`):** Singleton `Settings` loaded from `.env` via `python-dotenv`. Validates required env vars on init.

**Prompts (`prompts/system.py`):** All LLM system/classification prompts live here. Bot persona and response language is Korean (격식체).

## Key Conventions

- All LLM prompts and bot responses are in Korean.
- The `bctone.memories` table has categories: `progress`, `decision`, `todo`. Progress entries expire after 14 days; decisions don't expire; completed TODOs expire after 7 days.
- Tests mock all external dependencies (Anthropic API, PostgreSQL, GitHub, Slack) using `unittest.mock.patch`. The `conftest.py` autouse fixture resets the config singleton between tests.
- No ORM — all database access is raw SQL with `psycopg2`. Keep it that way.

## Environment Variables

See `.env.example` for the full list. Required: `SLACK_APP_TOKEN`, `SLACK_BOT_TOKEN`, `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`, `BCTONE_DB_URL`, `BOT_LOG_CHANNEL_ID`.
