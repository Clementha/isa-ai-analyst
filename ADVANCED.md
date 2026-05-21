# Advanced Configuration & Maintenance

This guide is for developers and technically confident users who want to go beyond the setup script — editing configuration files directly, running a local AI model, or managing updates via Git.

---

## Contents

- [Portfolio Config Reference](#-portfolio-config-reference)
- [Environment Variable Reference](#-environment-variable-reference)
- [Choosing a brain for your bot](#-choosing-a-brain-for-your-bot)
- [Trading 212 Account Type](#-trading-212-account-type)
- [Running Costs](#-running-costs)
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

## 🏦 Trading 212 Account Type

The setup guide recommends using a **STOCKS ISA** account on Trading 212 — this is the intended account type for this bot, and the one it has been tested with.

Advanced users may choose to point the bot at a different T212 account type (e.g. **Invest** — a general investment account). The trick is straightforward: when you generate your API key inside the Trading 212 app, generate it from within the account you want the bot to manage. The API key is scoped to the account it was created in.

Simply paste the corresponding API key during setup (option **2** on `setup.bat`) and the bot will read positions and cash from that account instead.

> ⚠️ **Tax implications vary by account type.** The ISA wrapper gives you tax-free gains. A general Invest account does not. The bot's analysis and recommendations are the same either way — but ensure you understand the tax treatment of the account you are using before trading.

---

## 🤖 Choosing a brain for your bot

ISA AI Analyst uses **[Claude Haiku 4.5](https://openrouter.ai/anthropic/claude-haiku-4-5) via OpenRouter** as its AI engine. This model was chosen for its speed, strong instruction-following, and cost-effectiveness — handling the conversational interface, news risk analysis, and ticker resolution at a low cost (~US$2–3/month for typical usage).

To switch to a different model available on OpenRouter:

**1.** Edit your `.env` file and update the model variable:

```env
LLM_MODEL="your-chosen-model-id"
```

Browse available models at [openrouter.ai/models](https://openrouter.ai/models).

**2.** Apply the new model to the OpenClaw conversational agent by running this command in any terminal:

```bash
docker exec isa_ai_analyst openclaw config set agents.defaults.model.primary "your-chosen-model-id"
```

**3.** Restart the bot to pick up both changes:

```bash
docker compose restart
```

> **Note:** You can also run **option 5 (Run Initial Setup)** on `setup.bat` to re-apply the default model (Claude Haiku 4.5) if you want to reset to the tested configuration.

> ⚠️ **Switching to a different model is untested.** The prompts, safety filters, and conversational flows have been tuned specifically for Claude Haiku 4.5. Other models — even capable ones like GPT-4o or Claude Opus — may behave differently, misinterpret commands, or produce unexpected output. If you choose to experiment, you are on your own. The setup script will always restore Claude Haiku 4.5 if you re-run option 5.

---

## 💸 Running Costs

### API Costs

The dominant running cost is OpenClaw's **agent heartbeat** — a keep-alive LLM call sent every ~30 minutes to check for tasks, regardless of whether you are actively using the bot. At default settings this accounts for the majority of daily API spend (~US$2–3/month).

We deliberately kept the heartbeat enabled. OpenClaw is an open platform, and the heartbeat is what makes it possible to build future capabilities on top of this bot — things like email check-ins, proactive alerts, or custom commands you define yourself. If you plan to extend the bot beyond scheduled ISA reports, the heartbeat is what makes that possible.

That said, advanced users who prefer a leaner setup — pure scheduled reports with no proactive agent features — can reduce or disable this cadence:

```bash
# Reduce heartbeat to every 2 hours
openclaw config set heartbeat.cadence "120"

# Disable entirely
openclaw config set heartbeat.cadence "0"
```

> ⚠️ **Disabling the heartbeat removes all proactive OpenClaw agent capabilities** — email check-ins, calendar reminders, and any other background monitoring tasks you may have configured. If you are using the bot purely for ISA reports and nothing else, this is safe to do. If you plan to extend it with other agent features, leave it enabled.

The report generation itself (the two daily analysis runs) costs a small fraction of the total — roughly US$0.001 per report.

---

### Hardware & Electricity

The ISA AI Analyst runs as a lightweight Docker container — it uses very little CPU and barely any memory when idle. Any modern Windows or Mac computer will run it fine.

> ⚠️ **The bot only works while your machine is awake.** If your computer is sleeping at 08:30 or 17:30, that report is missed entirely. Make sure your machine is set to stay awake during the scheduled report windows, or configure it to never sleep while Docker is running. This is one of the key motivations behind the [planned cloud service](#️-managed-cloud-service) in the Roadmap.

If you plan to run it **24/7 as an always-on home server**, hardware choice has a meaningful impact on your electricity bill:

| Device | Architecture | Avg. watts | Electricity cost (UK, per year) |
|---|---|---|---|
| **Mac mini M4** ⭐ | ARM64 (Apple Silicon) | ~10W | **~£24/yr** |
| Intel NUC 13 Pro | x86-64 | ~20W | ~£47/yr |
| Standard desktop PC | x86-64 | ~100W | ~£237/yr |
| Gaming/high-end PC | x86-64 | ~200W | ~£473/yr |

> Electricity cost calculated at UK average rate of ~27p/kWh, continuous 24/7 operation.

The **Mac mini M4** (from ~£650) idles at just **4W** — making it the ideal dedicated host for this project. Over 3 years, the electricity savings versus a standard desktop PC (~£639) effectively pay for the hardware itself.

### Minimum Requirements

| | Windows | macOS |
|---|---|---|
| **OS** | Windows 10/11 (64-bit) | macOS 12 Monterey or later |
| **CPU** | x86-64 (Intel or AMD) | Apple Silicon or Intel |
| **RAM** | 8 GB minimum, 16 GB recommended | 8 GB minimum |
| **Storage** | 10 GB free | 10 GB free |
| **Required** | Docker Desktop + WSL2 | Docker Desktop |

> **Windows users:** Download Docker Desktop for **AMD64** — this covers both Intel and AMD processors. Only select ARM64 if you have a Qualcomm Snapdragon device (e.g. Surface Pro X).

---

## 🔄 Updating & Maintenance

> ℹ️ **Folder name:** When downloaded from GitHub as a ZIP, the project extracts as `isa-ai-analyst-main`. All commands below use this name — do not rename the folder.

### First-Time Git Setup — Windows

If you installed ISA AI Analyst via ZIP download and want to receive future updates automatically, you'll need to set up Git first.

**1. Install Git for Windows:**

Download from [git-scm.com/download/win](https://git-scm.com/download/win) and run the installer. Click **Next** through all defaults — the defaults are correct for most users.

**2. Open Git Bash** (installed with Git) or **PowerShell**, navigate to your project folder, and initialise Git:

```bash
cd C:\Users\YourName\Documents\isa-ai-analyst-main
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
cd ~/Documents/isa-ai-analyst-main
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

Some changes require a full rebuild rather than a plain `start`. For example, if you edited `app/math_engine.py`, modified `requirements.txt`, or changed the `Dockerfile`, Docker needs to bake those changes into a new image:

```bash
docker compose down
docker compose up -d --build
```

A plain `docker compose start` after a `stop` reuses the existing image — it will not pick up any changes to Python source files or dependencies.
