# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

An autonomous AI-powered investment analyst for UK Tax-Free ISA accounts. It runs in Docker, sends twice-daily portfolio analysis via Telegram, and outputs buy/sell/hold recommendations gated by three safety checks: SMA trend, volatility, and AI-powered news risk screening. It does not execute trades — it is advisory only.

## Dev Commands

```bash
# Run the math engine directly (local test — does NOT send to Telegram by default)
python3 app/math_engine.py

# Install local dependencies for testing
pip install requests schedule

# Full stack (Docker)
docker compose up -d --build
docker compose logs -f
docker compose stop

# Emergency reset (wipes container state, keeps .env and portfolio config)
docker compose down --volumes --rmi all && docker compose up -d --build
```

There is no linting or test suite. Testing is done by running `math_engine.py` directly.

## Architecture

Two Python scripts run inside a Docker container alongside an OpenClaw (Node.js) agent:

**`app/scheduler.py`** — Background loop (fires every 60s). Reads `openclaw_data/workspace/HEARTBEAT.md` for scheduled times (default 08:30 & 16:00 UK). Spawns `math_engine.py` at those times. Implements a single-instance lock to prevent duplicate runs. Silently skips weekends.

**`app/math_engine.py`** — Core analysis engine. Calls three external APIs (Trading 212 for portfolio positions, EODHD for market data/news, OpenRouter for LLM analysis), applies the 3-gate filter, runs DCA logic, generates a Markdown report, saves it to `app/portfolio.md`, and pushes it to Telegram.

**OpenClaw Agent** — Node.js process that runs the Telegram bot. Handles natural-language commands ("Add Scottish Mortgage at 25%", "Run it now.", "What's my schedule?"), manages portfolio config JSON, resolves tickers, and hot-reloads `HEARTBEAT.md` to change the schedule without restarting the container.

## The 3-Gate Safety Filter

All three gates must be GREEN simultaneously (AND logic, not OR). One red = no buy recommendation, no matter how attractive the price looks.

1. **SMA Gate** — Current price > 20-day SMA
2. **Volatility Gate** — Daily price change < 5%
3. **News Gate** — LLM analysis of recent headlines for severe risks (fraud, lawsuits, credit downgrades). Favors false positives (better to miss a gain than take a loss).

**Do not bypass or weaken this logic for any reason.**

## Configuration

| File | Purpose |
|------|---------|
| `.env` | All API credentials (see below) |
| `app/portfolio_targets.json` | Holdings, target allocations %, ISA cash balance, DCA daily limits |
| `openclaw_data/workspace/HEARTBEAT.md` | Current schedule times (hot-reloaded by scheduler) |
| `config/IDENTITY.md` | Agent system prompt (synced to `openclaw_data/workspace/`) |
| `config/USER.md` | User profile for agent context |

## Required Environment Variables

```
T212_KEY_ID / T212_SECRET        Trading 212 API (read-only)
EODHD_API_KEY                    Market data + news
LLM_API_KEY / OPENROUTER_API_KEY OpenRouter (same key, both required)
LLM_MODEL                        e.g. openrouter/openai/gpt-4o-mini
LLM_BASE_URL                     OpenRouter endpoint
TELEGRAM_BOT_TOKEN               From @BotFather
TELEGRAM_CHAT_ID                 User's personal chat ID
```

Local LLM override: set `LLM_BASE_URL=http://host.docker.internal:11434/v1/chat/completions`, `LLM_MODEL=qwen2.5:32b`, `LLM_API_KEY=ollama`.

## Key Conventions

- All external API calls must be wrapped in try/except — failures should skip gracefully, not crash.
- Use `get_secret()` (defined in `math_engine.py`) for any API key access, never hardcode.
- The math engine must only run when explicitly triggered (scheduler time or "Run it now." command) — never on import or startup.
- Portfolio config overwrites require the user to confirm with the exact string "YES" before the agent applies changes.
- EODHD free tier supports ~3 stocks comfortably (20 calls/day limit). Keep this in mind when extending the analysis.
- Preserve emoji in report output — they are part of the intentional UX.

## Branch & PR Conventions

Feature branches: `feat/*`, bug fixes: `fix/*`, docs: `docs/*`, refactors: `refactor/*`. PRs should update README.md if new `.env` variables or report format changes are introduced.
