# 📈 IsaInvestClaw

> **Capital preservation is the primary directive.**

IsaInvestClaw is an autonomous, AI-powered quantitative analysis engine built specifically for **UK Tax-Free ISA accounts**. Powered by the OpenClaw framework, it runs locally, fetches daily market data, grades financial news, and delivers strict, conservative trade recommendations directly to your Telegram. You can chat with the bot naturally to update your portfolio structure or tune your daily reporting schedule.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform: macOS](https://img.shields.io/badge/Platform-macOS-blue.svg)](https://www.apple.com/macos/)
[![Runs on Docker](https://img.shields.io/badge/Runs%20on-Docker-2496ED?logo=docker&logoColor=white)](https://www.docker.com/products/docker-desktop/)
[![Telegram Bot](https://img.shields.io/badge/Interface-Telegram-26A5E4?logo=telegram&logoColor=white)](https://telegram.org/)

---

## 📋 Table of Contents

- [Features](#️-core-features)
- [Security & Protection](#️-built-in-security--protection-layers)
- [Prerequisites](#️-prerequisites--recommended-tools)
- [Quick Start](#-quick-start-installation-guide)
  - [1. Clone the Repository](#1-download-the-code)
  - [2. Set Up Your Telegram Bot](#2-set-up-your-telegram-bot)
  - [3. Configure Secrets](#3-configure-your-secrets-env-file)
  - [4. Set Portfolio Targets](#4-set-your-portfolio-targets)
  - [5. Launch the Engine](#5-launch-the-engine)
  - [6. Talk to Your Bot](#6-talk-to-your-bot)
- [Environment Variable Reference](#-environment-variable-reference)
- [Portfolio Config Reference](#-portfolio-config-reference)
- [Updating & Maintenance](#-updating--maintenance)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)
- [Disclaimer](#️-disclaimer)

---

## ⚙️ Core Features

| Feature | Description |
|---|---|
| 🤖 **100% Autonomous** | Runs automatically at configurable times (default: 10:30 & 22:30 UK time) |
| 📰 **AI News Risk Manager** | Uses LLMs to scan daily headlines and block trades if severe fundamental risks (fraud, lawsuits) are detected |
| 🔒 **Fail-Secure Architecture** | If the market is closed (weekends) or an API goes down, the bot safely skips execution |
| 📱 **Telegram Integration** | Actionable Markdown reports pushed straight to your phone |
| 💬 **Natural Language Control** | Chat with the bot to update your portfolio or adjust the schedule |

---

## 🛡️ Built-In Security & Protection Layers

IsaInvestClaw is built with strict safety boundaries to protect both your machine and your capital.

- **Isolated & Containerised:** The bot runs entirely inside a Docker container. It cannot see, access, or alter your host operating system. You can start, stop, or delete it without affecting your computer in any way.
- **No Direct Trade Execution:** The bot will never have access to your trading account password. It cannot perform trades autonomously — it only prepares recommendations based on read-only API permissions.
- **Cost-Capped AI:** Even if the AI enters an unexpected loop, usage is restricted to your available API credits. You are responsible for setting hard billing limits in your API provider accounts to prevent unexpected charges.

---

## 🛠️ Prerequisites & Recommended Tools

> **Platform note:** This setup guide is currently designed for **macOS**. Linux support is planned.

### Software to Install

1. **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** — Runs the bot in its secure container
2. **[Visual Studio Code](https://code.visualstudio.com/)** — A free editor to safely configure your settings
3. **[Telegram](https://telegram.org/)** — Download the app on your phone and Mac to communicate with the bot

### Required Accounts & API Keys

> *Note: Some links below are affiliate links. Using them helps support the continued open-source development of IsaInvestClaw at no extra cost to you.*

| Service | Purpose | Link |
|---|---|---|
| **Trading 212** | Free UK ISA brokerage with API access | [Sign Up](https://www.trading212.com/invite/4DtCF9r91Ms) |
| **EODHD APIs** | End-of-day pricing and financial news data | [Sign Up](https://eodhd.com?via=clementha) |
| **Novita AI** | LLM provider powering the bot's "brain" | [Sign Up](https://novita.ai/?ref=zmyynju&utm_source=affiliate) |

---

## 🚀 Quick Start Installation Guide

### 1. Download the Code

Open your Mac's **Terminal** and run:

```bash
git clone https://github.com/yourusername/IsaInvestClaw.git
cd IsaInvestClaw
```

---

### 2. Set Up Your Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send the command `/newbot`, give it a name, and copy the **Bot Token** it provides
3. To get your **Chat ID**, search for **@userinfobot** in Telegram, click Start, and copy the ID number shown

---

### 3. Configure Your Secrets (`.env` file)

1. Open the `IsaInvestClaw` folder in **Visual Studio Code**
2. Find the file named `.env.example`
3. Duplicate it and rename the copy to `.env`
4. Fill in your API keys and Telegram credentials

```bash
# Shortcut — do this in Terminal:
cp .env.example .env
code .env
```

Your completed `.env` should look like this:

```env
# --- AI Provider Settings ---
LLM_BASE_URL="https://api.novita.ai/v3/openai/chat/completions"
LLM_MODEL="kimi-k2.5"
LLM_API_KEY="your_novita_api_key_here"

# --- Financial APIs ---
EODHD_API_KEY="your_eodhd_key_here"
T212_KEY_ID="your_t212_key_id"
T212_SECRET="your_t212_secret"

# --- Telegram Bot ---
TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
TELEGRAM_CHAT_ID="your_telegram_chat_id"
```

> 🔒 **Security Note:** Never paste your API keys into the Telegram chat. Always store them in the local `.env` file only. See the [Environment Variable Reference](#-environment-variable-reference) below.

---

### 4. Set Your Portfolio Targets

Copy the example portfolio config and edit it to reflect your holdings, cash reserve, and run schedule:

```bash
cp config/portfolio_targets.example.json app/portfolio_targets.json
code app/portfolio_targets.json
```

Your config file will look like this:

```json
{
  "isa_allowance_target": 20000,
  "target_cash_pct": 0.25,
  "run_times": ["10:30", "22:30"],
  "holdings": {
    "VOD.LSE": 0.15,
    "BT-A.LSE": 0.15,
    "NWG.LSE": 0.15,
    "LLOY.LSE": 0.15,
    "LGEN.LSE": 0.15
  }
}
```

See the [Portfolio Config Reference](#-portfolio-config-reference) below for a full explanation of each field.

---

### 5. Launch the Engine

Make sure **Docker Desktop** is open and running, then in Terminal:

```bash
docker compose up -d
```

> The `-d` flag runs the engine quietly in the background. To view live logs, run:
> ```bash
> docker compose logs -f
> ```

---

### 6. Talk to Your Bot

Open Telegram and message your new bot. Here are some useful prompts to get started:

| Message | Action |
|---|---|
| `What is my current schedule?` | Shows the configured run times (default: 10:30 & 22:30 UK) |
| `Run it now.` | Triggers an immediate manual report |
| `Update my portfolio targets.` | Begins a guided portfolio rebalancing flow |
| `Pause reporting.` | Suspends automatic daily reports |

---

## 🔑 Environment Variable Reference

Full reference for all variables in your `.env` file:

| Variable | Required | Description |
|---|---|---|
| `LLM_BASE_URL` | ✅ | The OpenAI-compatible endpoint for your LLM provider |
| `LLM_MODEL` | ✅ | The model name to use (e.g. `kimi-k2.5`) |
| `LLM_API_KEY` | ✅ | Your Novita AI API key |
| `EODHD_API_KEY` | ✅ | Your EODHD market data API key |
| `T212_KEY_ID` | ✅ | Your Trading 212 API Key ID |
| `T212_SECRET` | ✅ | Your Trading 212 API Secret |
| `TELEGRAM_BOT_TOKEN` | ✅ | Token from @BotFather |
| `TELEGRAM_CHAT_ID` | ✅ | Your personal chat ID from @userinfobot |

---

## 📊 Portfolio Config Reference

Full reference for all fields in `app/portfolio_targets.json`:

| Field | Type | Description |
|---|---|---|
| `isa_allowance_target` | `number` | Your total ISA allowance for the tax year in GBP (e.g. `20000`) |
| `target_cash_pct` | `number` | Fraction of the portfolio to keep as cash reserve (e.g. `0.25` = 25%) |
| `run_times` | `array` | UTC+1 times to run the engine each day (e.g. `["10:30", "22:30"]`) |
| `holdings` | `object` | Map of ticker symbols to target portfolio weight. Weights should sum to `1.0` minus `target_cash_pct` |

> ℹ️ **Ticker format:** Use the EODHD format — `SYMBOL.EXCHANGE` (e.g. `VOD.LSE` for Vodafone on the London Stock Exchange).

---

## 🔄 Updating & Maintenance

To pull the latest version and restart cleanly:

```bash
git pull origin main
docker compose down
docker compose up -d --build
```

To stop the bot without removing your configuration:

```bash
docker compose stop
```

To completely remove all containers and free up disk space:

```bash
docker compose down --volumes --rmi all
```

---

## 🩺 Troubleshooting

**Bot is not responding on Telegram**
- Confirm that Docker is running: `docker compose ps`
- Check logs for errors: `docker compose logs -f`
- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are correct in `.env`

**"API Key invalid" error in logs**
- Double-check you copied the full key with no trailing spaces into `.env`
- Ensure your EODHD or Novita account subscription is active
- Confirm `T212_KEY_ID` and `T212_SECRET` are both filled in (both are required)

**Reports not arriving at scheduled times**
- Confirm your system clock and timezone are correct (the bot uses your Docker host's time)
- Check your `run_times` values in `app/portfolio_targets.json` are in UK local time (UTC+1 during BST)
- Test immediately with `Run it now.` in the Telegram chat

**Docker Desktop won't start on Apple Silicon**
- Ensure Rosetta 2 is installed: `softwareupdate --install-rosetta`

---

## 📝 License

This project is open-source and available under the [MIT License](LICENSE).

---

## ⚠️ Disclaimer

This software is provided for **educational and informational purposes only**. It does not constitute financial advice. The AI can hallucinate, and market data APIs can return incorrect data. **Always verify recommendations manually before taking any action.** Never risk capital you cannot afford to lose. Past performance is not indicative of future results.
