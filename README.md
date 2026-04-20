# 📈 IsaInvestClaw

> **Capital preservation is the primary directive.**

IsaInvestClaw is an autonomous, AI-powered quantitative analysis engine built specifically for **UK Tax-Free ISA accounts**. Powered by the OpenClaw framework, it runs locally, fetches daily market data, grades financial news, and delivers strict, conservative trade recommendations directly to your Telegram. You define which stocks to track and at what target allocations — the bot does the rest. You can chat with it naturally to update your portfolio structure or tune your daily reporting schedule.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform: macOS](https://img.shields.io/badge/Platform-macOS-blue.svg)](https://www.apple.com/macos/)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078D4?logo=windows&logoColor=white)](https://www.docker.com/products/docker-desktop/)
[![Runs on Docker](https://img.shields.io/badge/Runs%20on-Docker-2496ED?logo=docker&logoColor=white)](https://www.docker.com/products/docker-desktop/)
[![Telegram Bot](https://img.shields.io/badge/Interface-Telegram-26A5E4?logo=telegram&logoColor=white)](https://telegram.org/)

---

## 📺 Video Walkthrough

> 🎬 A full step-by-step video setup guide is available on YouTube. Watch it alongside this README for the smoothest experience.

[![Watch the IsaInvestClaw Setup Guide on YouTube](https://img.youtube.com/vi/YOUTUBE_VIDEO_ID/maxresdefault.jpg)](https://www.youtube.com/watch?v=YOUTUBE_VIDEO_ID)

**Jump to a specific section:**

| Timestamp | Section |
|---|---|
| [0:00](https://youtu.be/YOUTUBE_VIDEO_ID?t=0) | Introduction & Overview |
| [2:00](https://youtu.be/YOUTUBE_VIDEO_ID?t=120) | Installing Prerequisites (Docker, VS Code, Telegram) |
| [5:00](https://youtu.be/YOUTUBE_VIDEO_ID?t=300) | Step A — Clone the Repository |
| [7:00](https://youtu.be/YOUTUBE_VIDEO_ID?t=420) | Step B — Create Your `.env` File |
| [9:00](https://youtu.be/YOUTUBE_VIDEO_ID?t=540) | Step C — Create Accounts & Gather API Keys |
| [20:00](https://youtu.be/YOUTUBE_VIDEO_ID?t=1200) | Step D — Fill In Your `.env` File |
| [22:00](https://youtu.be/YOUTUBE_VIDEO_ID?t=1320) | Step E — Set Up Your Telegram Bot |
| [25:00](https://youtu.be/YOUTUBE_VIDEO_ID?t=1500) | Step F — Set Portfolio Targets |
| [28:00](https://youtu.be/YOUTUBE_VIDEO_ID?t=1680) | Step G — Launch the Engine |
| [30:00](https://youtu.be/YOUTUBE_VIDEO_ID?t=1800) | Step H — Pair Your Telegram Bot |
| [33:00](https://youtu.be/YOUTUBE_VIDEO_ID?t=1980) | Step I — First Run & Talking to Your Bot |

---

## 📋 Table of Contents

- [How It Works](#-how-it-works)
- [Features](#️-core-features)
- [Security & Protection](#️-built-in-security--protection-layers)
- [Prerequisites](#️-prerequisites--recommended-tools)
- [Quick Start](#-quick-start-installation-guide)
  - [A. Clone the Repository](#a-download-the-code)
  - [B. Create Your `.env` File](#b-create-your-env-file)
  - [C. Create Your Accounts & Gather API Keys](#c-create-your-accounts--gather-api-keys)
  - [D. Fill In Your `.env` File](#d-fill-in-your-env-file)
  - [E. Set Up Your Telegram Bot](#e-set-up-your-telegram-bot)
  - [F. Launch the Engine](#g-launch-the-engine)
  - [G. Pair Your Telegram Bot](#h-pair-your-telegram-bot)
  - [H. Talk to Your Bot](#i-talk-to-your-bot)
- [Environment Variable Reference](#-environment-variable-reference)
- [Portfolio Config Reference](#-portfolio-config-reference)
- [Updating & Maintenance](#-updating--maintenance)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)
- [Disclaimer](#️-disclaimer)
- [Good Luck & Support](#-good-luck--support-the-project)

---

## 🔍 How It Works

Before IsaInvestClaw runs, you define your **Portfolio Targets** — a simple JSON file where you specify which UK stocks you want to track, your target allocation percentage for each, your ISA allowance, and your desired cash reserve. This is the instruction sheet the AI works from.

At each scheduled run (default: 10:30 & 22:30 UK time), IsaInvestClaw:

1. **Reads your portfolio targets** from `app/portfolio_targets.json`
2. **Fetches live market data** from EODHD for every stock in your watchlist
3. **Scans financial news** for risk signals (fraud, lawsuits, earnings surprises)
4. **Compares your current holdings** via the Trading 212 read-only API against your targets
5. **Generates a Markdown report** and pushes it to your Telegram with trade suggestions

> See [Step F](#f-set-your-portfolio-targets) and the [Portfolio Config Reference](#-portfolio-config-reference) for how to configure your targets.

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

- **Isolated & Containerised:** The bot runs entirely inside a Docker container, with its own filesystem and process space completely separated from your host OS. It can only access files within the project folder that you explicitly mounted — it has no visibility into your macOS applications, other files, or system settings.†
- **No Direct Trade Execution:** The bot cannot perform trades autonomously, as it never has access to your trading account password. It only provides trade recommendations based on read-only API permissions.
- **Cost-Capped AI:** Even if the AI enters an unexpected loop, usage is restricted to your available API credits. You are responsible for setting hard billing limits in your API provider accounts to prevent unexpected charges.
- **Minimised Prompt Injection Risk:** The bot does not browse arbitrary web pages to gather news. It exclusively consumes structured financial data from EODHD, an industry-standard market data API. This means it is not exposed to maliciously crafted web content designed to manipulate AI behaviour — significantly reducing the risk of prompt injection attacks.

---

## 🛠️ Prerequisites & Recommended Tools

> **Platform support:** Full setup guide provided for **macOS**. **Windows** support via Docker Desktop and WSL2 is also supported — see the note in Step A below.

### Software to Install

1. **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** — Runs the bot in its secure container
2. **[Visual Studio Code](https://code.visualstudio.com/)** — A free editor to safely configure your settings
3. **[Telegram](https://telegram.org/)** — Download the app on your phone and Mac to communicate with the bot

### Accounts You Will Need

You will need accounts with **Trading 212**, **EODHD**, and **Novita AI**. Do not create them yet — [Step C](#c-create-your-accounts--gather-api-keys) of the Quick Start guide will walk you through each one in the right order, once your `.env` file is already open and ready to receive the keys.

---

## 🚀 Quick Start Installation Guide

### A. Download the Code

Open your Mac's **Terminal** and run:

```bash
git clone https://github.com/ClementHa/IsaInvestClaw.git
cd IsaInvestClaw
```

> **Windows users:** Install [Git for Windows](https://git-scm.com/download/win) and [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/) (requires WSL2). Then run the same commands above in **PowerShell** or **Windows Terminal**. All subsequent `docker compose` commands are identical.

---

### B. Create Your `.env` File

Before creating any accounts, create your secrets file so it is ready to fill in as you go:

```bash
cp .env.example .env
code .env
```

This opens the `.env` file in VS Code. Leave it open — you will paste your API keys into it during the next step.

> 🔒 **Security Note:** Never commit your `.env` file to Git. It is already listed in `.gitignore` by default — do not remove it.

---

### C. Create Your Accounts & Gather API Keys

Work through each service below in order. By the end of this step, all fields in your `.env` file will be filled in.

> *Note: Some links below are affiliate links. Using them helps support the continued open-source development of IsaInvestClaw at no extra cost to you.*

---

#### 🏦 Trading 212 — Free UK Stocks ISA with API Access

1. Click the affiliate link to sign up: **[Create Trading 212 Account](https://www.trading212.com/invite/4DtCF9r91Ms)**
2. Complete the registration form and verify your identity as prompted
3. When asked to choose an account type, select **Stocks ISA**
4. Once your account is open, tap **Add Funds** and make a deposit of at least **£1**

   > ⚠️ **This deposit is required.** The API (Beta) option will not appear in your settings until your ISA account has been funded at least once.

5. Go to **Settings** (the gear icon, bottom-right)
6. Scroll down and tap **API (Beta)**
7. Tap **Generate API Key**

   > 🔒 **Critical — Read Before Generating:**
   > When the permissions screen appears, you **MUST uncheck** the following two permissions:
   > - ❌ **Orders — Execute** *(uncheck this)*
   > - ❌ **Pies — Write** *(uncheck this)*
   >
   > IsaInvestClaw only reads your portfolio data — it never places trades. Leaving these permissions enabled means a compromised API key could place real trades on your account without your knowledge.

8. Trading 212 will display your **Key ID** and **Secret Key**. Paste both values immediately into your open `.env` file:
   ```env
   T212_KEY_ID="your_key_id_here"
   T212_SECRET="your_secret_here"
   ```
   > 🔒 The Secret Key is shown **only once**. If you lose it, you must revoke and regenerate the key.

---

#### 📊 EODHD — End-of-Day Market Data & Financial News

1. Click the affiliate link to sign up: **[Create EODHD Account](https://eodhd.com?via=clementha)**
2. Complete the registration form and verify your email address
3. Once logged in, go to your **Dashboard**
4. Your API key is shown at the top of the Dashboard under **Your API Token**
5. Click **Copy** and paste the key into your open `.env` file:
   ```env
   EODHD_API_KEY="your_eodhd_key_here"
   ```

   > ℹ️ **Free tier:** EODHD's free plan includes **20 API calls per day**. Each stock price lookup consumes 1 call, and each news fetch consumes 5 calls. This is sufficient for light users tracking a small number of stocks with twice-daily runs — but if you add many holdings or increase your run frequency, consider upgrading to a paid plan.

---

#### 🤖 Novita AI — LLM Provider (the Bot's "Brain")

1. Click the affiliate link to sign up: **[Create Novita AI Account](https://novita.ai/?ref=zmyynju&utm_source=affiliate)**
2. Complete the registration form and verify your email address
3. Go to **Billing** and add credits — a minimum of **USD $10** is recommended to get started comfortably

   > ℹ️ In our experience, USD $10 is typically enough for **more than a month** of light usage (a small portfolio, twice-daily runs). Your consumption will vary depending on the number of holdings and how often you chat with the bot.

4. While in Billing, set a **spending limit** to cap the maximum amount the AI can consume in a given period — this protects against unexpected costs if the bot enters an unexpected loop
5. Go to **API Keys** (in the left sidebar or account menu)
6. Click **Create API Key**, give it a name (e.g. `IsaInvestClaw`), and confirm
7. Copy the generated key and paste it into your open `.env` file:
   ```env
   LLM_API_KEY="your_novita_key_here"
   ```
   > 🔒 The API key is shown **only once** at creation. Store it securely.

---

### D. Fill In Your `.env` File

By now, all API keys should already be filled in from the previous step. Complete any remaining fields — your finished `.env` should look like this:

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

> The Telegram fields will be filled in the next step. See the [Environment Variable Reference](#-environment-variable-reference) for a full description of each field.

---

### E. Set Up Your Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send the command `/newbot`, give it a name, and copy the **Bot Token** it provides
3. Paste the token into your `.env` file as `TELEGRAM_BOT_TOKEN`
4. To get your **Chat ID**, search for **@userinfobot** in Telegram, click Start, and copy the ID number shown
5. Paste the ID into your `.env` file as `TELEGRAM_CHAT_ID`
6. Save and close the `.env` file

---

### F. Launch the Engine

Make sure **Docker Desktop** is open and running, then in Terminal:

```bash
docker compose up -d
```
*(The `-d` flag runs the engine quietly in the background.)*

**Verify the Launch (Health Check)**
To ensure the engine started successfully before moving to the next step, run:

```bash
docker ps
```

If you see `openclaw_invest_bot` in the list with a status of **Up**, the launch was successful!

> **Optional: Watch the Engine Start**
> If you want a peek behind the curtain to see what the bot is doing, run:
> 
> ```bash
> docker compose logs -f
> ```
> 
> *(Don't worry if the output looks like the Matrix or shows minor installation warnings on the first run—this is completely normal while it downloads its dependencies! You can press `Ctrl+C` to exit the log view at any time.)*

---

### G. Pair Your Telegram Bot

> This step is **required** before the bot will respond to anyone. OpenClaw uses a zero-trust pairing system — it ignores all messages until the owner explicitly approves a one-time pairing code. This prevents anyone who discovers your bot username from being able to issue commands to your AI.

**Here's how it works:**

1. Ensure your container is still running from Step F.
2. Open Telegram and search for your bot by the username you set in @BotFather (e.g. `@MyIsaClawBot`)
3. Send any message — `hello` is fine
4. The bot replies with a short alphanumeric pairing code, for example:
```env
Your pairing code is: Z2EDQKMK
Approve this code to continue.
```

5. Copy that code, go back to your **Terminal**, and run:
```bash
docker exec -it isa_invest_claw openclaw pairing approve telegram Z2EDQKMK
```
*(Replace `Z2EDQKMK` with the actual code the bot sent you)*
If successful, your terminal will output a confirmation message similar to:
Approved telegram sender "123456789" (with your actual Telegram Chat ID).

6. The bot confirms the connection — you're ready to go

> ⚠️ **Note:** You may need to repeat this pairing step if you restart the container or change your bot token. If the bot keeps generating a new pairing code on every message without accepting the approval, check the [Troubleshooting](#-troubleshooting) section below.

---

### H. Talk to Your Bot

Open Telegram and message your bot. Here are some useful prompts to get started:

| Message | Action |
|---|---|
| `What is my current schedule?` | Shows the configured run times (default: 10:30 & 22:30 UK) |
| `Run it now.` | Triggers an immediate manual report |
| `Update my portfolio targets.` | Begins a guided portfolio rebalancing flow |
| `Pause reporting.` | Suspends automatic daily reports |

---

### 🎉 Setup Complete — You're All Set!

Congratulations — IsaInvestClaw is now fully up and running! Here's what you've accomplished:

- ✅ A securely containerised AI engine running entirely on your own machine
- ✅ Read-only Trading 212 integration — no accidental trades are possible
- ✅ Twice-daily portfolio analysis with Telegram report delivery
- ✅ AI-powered financial news risk screening before every report
- ✅ Full natural language control via Telegram chat

Your bot will deliver its first scheduled report at the next run time (default: 10:30 or 22:30 UK). Can't wait? Send **`Run it now.`** on Telegram to trigger an immediate report right now.

If you found IsaInvestClaw useful, please consider [⭐ starring the repository](https://github.com/ClementHa/IsaInvestClaw) — it helps others discover the project and keeps development going.

---

## 🔑 Environment Variable Reference

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

| Field | Type | Description |
|---|---|---|
| `isa_allowance_target` | `number` | Your total ISA allowance for the tax year in GBP (e.g. `20000`) |
| `target_cash_pct` | `number` | Fraction of the portfolio to keep as cash reserve (e.g. `0.25` = 25%) |
| `holdings` | `object` | Map of T212 ticker symbols (e.g. `VOD_LSE_EQ`) to their mapped EODHD ticker, display name, and target weight. Weights should sum to `1.0` minus `target_cash_pct`. |

> ℹ️ **Note on Tickers:** You do not need to configure these manually. When you chat with the bot to add a stock, its internal engine automatically queries and maps the correct Trading 212 and EODHD identifiers for you.

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

**Bot sends a pairing code but never accepts the approval**
- This is a known OpenClaw issue when the container is restarted mid-session — the session state is lost
- Fix: stop the container fully (`docker compose down`), bring it back up (`docker compose up -d`), then redo the pairing step from scratch

**Bot is not responding on Telegram at all**
- Confirm that Docker is running: `docker compose ps`
- Check logs for errors: `docker compose logs -f`
- Ensure you completed the [pairing step](#h-pair-your-telegram-bot) — the bot will silently ignore all messages until pairing is approved
- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are correct in `.env`

**"API Key invalid" error in logs**
- Double-check you copied the full key with no trailing spaces into `.env`
- Ensure your EODHD or Novita account subscription is active
- Confirm both `T212_KEY_ID` and `T212_SECRET` are filled in (both are required)
- If your Trading 212 API key stopped working, check that your ISA account still has funds — a zero balance can deactivate API access

**Reports not arriving at scheduled times**
- Confirm your system clock and timezone are correct (the bot uses your Docker host's time)
- Test immediately with `Run it now.` in the Telegram chat

**Docker Desktop won't start on Apple Silicon**
- Ensure Rosetta 2 is installed: `softwareupdate --install-rosetta`

**Docker Desktop won't start on Windows**
- Ensure WSL2 is installed and enabled: run `wsl --install` in PowerShell (as Administrator)
- Enable WSL2 integration in Docker Desktop → Settings → Resources → WSL Integration

---

## 📝 License

This project is open-source and available under the [MIT License](LICENSE).

---

## ⚠️ Disclaimer

This software is provided for **educational and informational purposes only**. It does not constitute financial advice. The AI can hallucinate, and market data APIs can return incorrect data. **Always verify recommendations manually before taking any action.** Never risk capital you cannot afford to lose. Past performance is not indicative of future results.

---

## 🍀 Good Luck & Support the Project

Investing is part discipline, part patience — and a little bit of luck never hurts. We hope IsaInvestClaw helps you make more informed, confident decisions with your ISA.

If the bot has ever saved you from a bad trade, helped you spot an opportunity, or simply kept you better organised — consider buying us a coffee. Every contribution goes directly towards new features, better models, and keeping the project open-source and free.

[![Ko-fi](https://img.shields.io/badge/Support%20on-Ko--fi-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/clementha)

> *"The stock market is a device for transferring money from the impatient to the patient."* — Warren Buffett

Good luck out there. 📈

---

† No Docker container is a perfect security fortress. Containers share the host's network stack by default, meaning a severely compromised container — for example, one manipulated via prompt injection — could theoretically attempt to probe your host machine over the local Docker bridge network. This is an advanced and unlikely threat, but it is real. IsaInvestClaw does not mount the Docker socket and does not run in privileged mode, which significantly limits the blast radius of any such attack. For the vast majority of users, the container isolation is more than sufficient — but you should be aware it is not equivalent to a fully separate virtual machine.