# Advanced Configuration & Maintenance

This guide is for developers and technically confident users who want to go beyond the setup script — editing configuration files directly, running a local AI model, or managing updates via Git.

---

## Contents

- [Portfolio Config Reference](#-portfolio-config-reference)
- [Environment Variable Reference](#-environment-variable-reference)
- [Running with a Local LLM (Ollama)](#-running-with-a-local-llm-ollama)
- [Updating & Maintenance](#-updating--maintenance)

---

## 📊 Portfolio Config Reference

The portfolio configuration lives at `app/portfolio_targets.json`. You do not need to edit this file manually — the analyst manages it for you via Telegram chat. It is documented here for reference or if you want to bulk-edit it directly.

| Field | Type | Description |
|---|---|---|
| `isa_allowance_target` | `number` | Total ISA allowance for the tax year in GBP (e.g. `20000`) |
| `target_cash_pct` | `number` | Fraction of portfolio to keep as cash reserve (e.g. `0.25` = 25%) |
| `daily_dca_limit` | `number` | Maximum GBP to deploy per stock per day via DCA (e.g. `500`) |
| `holdings` | `object` | Map of T212 ticker keys to EODHD ticker, display name, and target weight |

**Example:**
```json
{
  "isa_allowance_target": 20000,
  "target_cash_pct": 0.25,
  "daily_dca_limit": 500,
  "holdings": {
    "VOD_LSE_EQ": {
      "eodhd_ticker": "VOD.LSE",
      "name": "Vodafone Group PLC",
      "target_weight": 0.25
    }
  }
}
```

> ℹ️ Ticker symbols are resolved automatically when you add a stock via Telegram. You never need to look them up manually.

---

## 🔑 Environment Variable Reference

All variables live in the `.env` file in the project root. The setup script writes this file for you, but you can edit it directly in any text editor.

| Variable | Required | Description |
|---|---|---|
| `LLM_BASE_URL` | ✅ | OpenAI-compatible endpoint (set automatically to OpenRouter) |
| `LLM_MODEL` | ✅ | Model name (set automatically by setup) |
| `LLM_API_KEY` | ✅ | Your OpenRouter API key |
| `OPENROUTER_API_KEY` | ✅ | Same key — required by some OpenClaw internals |
| `EODHD_API_KEY` | ✅ | Your EODHD market data API key |
| `T212_KEY_ID` | ✅ | Your Trading 212 API Key ID |
| `T212_SECRET` | ✅ | Your Trading 212 API Secret |
| `TELEGRAM_BOT_TOKEN` | ✅ | Token from @BotFather |
| `TELEGRAM_CHAT_ID` | ✅ | Your personal chat ID from @userinfobot |

---

## 🤖 Running with a Local LLM (Ollama)

ISA AI Analyst supports running with a **local LLM** via [Ollama](https://ollama.com/) or any other OpenAI-compatible inference server. This removes the need for an OpenRouter account entirely and eliminates AI API costs.

### Step 1 — Install Ollama

Download and install Ollama from [ollama.com](https://ollama.com/). It runs on macOS, Windows, and Linux.

### Step 2 — Pull a model

Open a terminal and pull a capable model. A 32B parameter model gives results closest to the hosted version:

```bash
ollama pull qwen2.5:32b
```

For machines with less RAM (< 16 GB), a smaller model works but may produce less nuanced news risk analysis:

```bash
ollama pull qwen2.5:7b
```

Verify Ollama is running:

```bash
ollama list
```

### Step 3 — Edit your `.env` file

Open the `.env` file in the project folder in any text editor and override these three variables:

```env
LLM_BASE_URL="http://host.docker.internal:11434/v1/chat/completions"
LLM_MODEL="qwen2.5:32b"
LLM_API_KEY="ollama"
```

> ℹ️ `host.docker.internal` is how Docker containers reach services running on your host machine. This works on macOS and Windows out of the box. On Linux, you may need to add `--add-host=host.docker.internal:host-gateway` to your Docker run command or use your host's actual LAN IP instead.

### Step 4 — Restart the container

```bash
docker compose down
docker compose up -d --build
```

The `Set AI API Key (OpenRouter)` step in the setup script can be skipped entirely when using a local model.

### Using other OpenAI-compatible servers

Any OpenAI-compatible inference server works. Adjust `LLM_BASE_URL` and `LLM_MODEL` to match your server's endpoint and model name. Examples:

| Server | `LLM_BASE_URL` | `LLM_MODEL` |
|---|---|---|
| Ollama | `http://host.docker.internal:11434/v1/chat/completions` | `qwen2.5:32b` |
| LM Studio | `http://host.docker.internal:1234/v1/chat/completions` | your loaded model name |
| vLLM | your server's endpoint | your deployed model name |

---

## 🔄 Updating & Maintenance

### First-Time Git Setup — Windows

If you installed ISA AI Analyst via ZIP download and want to receive future updates automatically, you'll need to set up Git first.

**1. Install Git for Windows:**

Download from [git-scm.com/download/win](https://git-scm.com/download/win) and run the installer. Click **Next** through all defaults — the defaults are correct for most users.

**2. Open Git Bash** (installed with Git) or **PowerShell**, navigate to your project folder, and initialise Git:

```bash
cd C:\Users\YourName\Documents\isa-ai-analyst
git init
git remote add origin https://github.com/Clementha/isa-ai-analyst.git
git fetch origin
git checkout main
```

**3. Configure your Git identity** (required for Git to work):

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

---

### First-Time Git Setup — macOS

Git is pre-installed on macOS. If you installed via ZIP and want to pull future updates:

**1. Open Terminal**, navigate to your project folder, and initialise Git:

```bash
cd ~/Documents/isa-ai-analyst
git init
git remote add origin https://github.com/Clementha/isa-ai-analyst.git
git fetch origin
git checkout main
```

**2. Configure your Git identity:**

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

> ℹ️ If prompted to install Xcode Command Line Tools, click **Install** and wait for it to complete, then re-run the commands above.

---

### Pulling Updates

Once Git is set up, pull the latest version and restart the container:

```bash
git pull origin main
docker compose down
docker compose up -d --build
```

The `--build` flag forces Docker to rebuild the image with the updated code. Wait for the logs to show the agent is running before using Telegram:

```bash
docker compose logs -f
```

Press `Ctrl+C` to stop following the logs once you see the agent is ready.

### Stopping the Bot

To stop the analyst without removing any configuration or data:

| 🪟 Windows | 🍎 macOS / Linux |
|---|---|
| Run `setup.bat` → select option **7** | Run `bash setup.sh` → select option **7** |

Or from any terminal:

```bash
docker compose stop
```

### Restarting After a Stop

To bring the bot back up after a `stop` (no rebuild needed — your data is intact):

```bash
docker compose start
```

Or use the setup script (option **6 — Start Agent**) on either platform.

> ℹ️ Use `docker compose stop` / `start` for routine on/off. Use `docker compose down` / `up -d --build` only when you've pulled an update or want a clean restart.
