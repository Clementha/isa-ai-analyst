# 📈 ISA AI Analyst

> Your always-on ISA analyst. Invest with confidence.

ISA AI Analyst is an autonomous, AI-powered **investment analyst** built specifically for **UK Tax-Free ISA accounts**. Think of it as a helpful data assistant that works quietly in the background — analysing your portfolio every day, screening financial news for risk, and delivering clear, data-driven insights directly to your Telegram so you can make better-informed investment decisions without spending hours researching. It is built on a single principle: **capital preservation first**.

The bot is designed to address two of the biggest challenges for retail investors: **emotional decision-making** (panic-selling on bad news, chasing momentum) and **information overload** (not having time to read the news on every stock you hold). ISA AI Analyst handles both, so you only act when the data says it makes sense to.

Powered by the [OpenClaw](https://openclaw.ai) framework, it runs entirely on your own machine inside a secure Docker container.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078D4?logo=windows&logoColor=white)](https://www.docker.com/products/docker-desktop/)
[![Platform: macOS](https://img.shields.io/badge/Platform-macOS-blue.svg)](https://www.apple.com/macos/)
[![Runs on Docker](https://img.shields.io/badge/Runs%20on-Docker-2496ED?logo=docker&logoColor=white)](https://www.docker.com/products/docker-desktop/)
[![Telegram Bot](https://img.shields.io/badge/Interface-Telegram-26A5E4?logo=telegram&logoColor=white)](https://telegram.org/)

---

## 📊 Example Report

*The analyst delivers two reports per day — a morning briefing and an evening analysis:*

<!-- SCREENSHOT: Example Telegram report output showing portfolio analysis, trade suggestions, and news risk summary -->
<img src="docs/screenshots/telegram-report-example.png" alt="Example ISA AI Analyst Telegram report" width="500" />

**Morning Briefing (08:30)** — pre-market context based on the previous close:

```
=== 🌅 MORNING BRIEFING ===
06 May 2026 | Prices as of previous close

Portfolio Value: £12,450.00
------------------------------

🔹 Vodafone Group PLC (VOD_LSE_EQ / VOD.LSE) | Close: £74.32 (Mon 05 May)
Holding: 21.3% (£4,260.00) → Target: 25%
Gates: SMA 👍 | Vol 👍 | News 👍
Outlook: 🟢 GREEN
Overnight News:
 - [05 May] Vodafone completes network expansion deal with BT
 - [04 May] Analysts raise price target following dividend confirmation
```

**Evening Analysis (17:30)** — actionable recommendations using today's confirmed closing prices:

```
=== 📊 EVENING ANALYSIS ===
06 May 2026 | Today's closing prices

Total Value: £12,480.00
Target Cash: 25.0%
------------------------------

🔹 Vodafone Group PLC (VOD_LSE_EQ / VOD.LSE) | Close: £74.86 (Tue 06 May)
Target: 25% (£5,000.00) | Current: 21.1% (£4,280.00)
Signal: 🟢 GREEN [BUY £500.00 (DCA mode, £720.00 total gap)]
Gates: SMA 👍 | Vol 👍 | News 👍
Today's News:
 - [06 May] Vodafone completes network expansion deal with BT
 - [04 May] Analysts raise price target following dividend confirmation
 - [03 May] Telecoms sector outperforms FTSE 100 for third consecutive week
```

### Reading the Report

| Symbol | Meaning |
|---|---|
| 🟢 GREEN | All 3 safety gates passed — a BUY or HOLD action is suggested |
| 🔴 RED | One or more gates failed — action is SELL or AVOID |
| 👍 | That individual gate passed |
| 👎 | That individual gate failed — this is what triggered a RED signal |
| 🤷 | No recent news found — news gate skipped, not counted as a fail |
| ⚠️ | News gate could not be evaluated (AI API error) — treated as a fail |

---

## 🧠 Investment Strategy

ISA AI Analyst applies two well-established, conservative investment strategies automatically on every report.

### The 3 Safety Gates

Before issuing any BUY recommendation, the analyst requires a stock to pass **three independent checks** simultaneously. If any gate fails, no action is recommended — regardless of how attractive the price looks.

| Gate | Check | Why It Matters |
|---|---|---|
| **Trend** | Current price must be above the Simple Moving Average (SMA) | Avoids buying into a confirmed downtrend |
| **Volatility** | Daily volatility must be strictly under 5% | Avoids entering during high-turbulence periods where price swings are driven by noise rather than fundamentals |
| **News** | AI scans recent headlines and summaries (with publication dates) and blocks entry if severe fundamental risks are detected (fraud, lawsuits, profit warnings, regulatory action) | Protects against value traps — stocks that look cheap on price but are deteriorating fundamentally |

All three gates must be green simultaneously. One red gate = no recommendation.

### Dollar-Cost Averaging (DCA)

Rather than deploying capital in a single lump sum, ISA AI Analyst scales into positions gradually up to a configurable **daily DCA limit** (e.g. £500/day). This smooths out the impact of short-term price volatility and removes the pressure of trying to time the perfect entry point.

---

## 📋 Table of Contents

- [How It Works](#-how-it-works)
- [Core Features](#️-core-features)
- [Security & Protection](#️-built-in-security--protection-layers)
- [Prerequisites](#️-prerequisites)
- [Quick Start](#-quick-start)
- [EODHD Free Tier Limits](#-eodhd-free-tier-limits)
- [Emergency Reset (Nuke & Restart)](#-emergency-reset-nuke--restart)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

> 🛠️ **Developers & power users:** see [ADVANCED.md](ADVANCED.md) for portfolio config reference, environment variables, running a local LLM (Ollama), and Git-based update instructions.
- [Disclaimer](#️-disclaimer)
- [Support the Project](#-good-luck--support-the-project)

---

## 🔍 How It Works

The analyst runs twice a day at default times of **08:30 and 17:30 UK time**:

- **Morning Briefing (08:30)** — uses the previous day's closing prices to flag overnight news risks and give you a market-open context before you start your day.
- **Evening Analysis (17:30)** — runs after LSE closes at 16:30, using today's confirmed closing prices to produce the actionable BUY/SELL/HOLD recommendations you act on the next morning.

At each report, it:

1. **Reads your portfolio targets** — the stocks you want to hold and at what allocations
2. **Fetches market data** from EODHD for every stock in your watchlist
3. **Applies the 3 Safety Gates** — trend, volatility, and news checks for each holding
4. **Compares your current holdings** via the Trading 212 read-only API against your targets
5. **Generates a report** and pushes it directly to your Telegram

You can also chat with the analyst at any time in plain English to update your portfolio, change your schedule, trigger an immediate report, or ask for the latest price and news on any stock you hold.

---

## ⚙️ Core Features

| Feature | Description |
|---|---|
| 🤖 **100% Autonomous** | Runs automatically at configurable times (default: 08:30 morning briefing & 17:30 evening analysis, UK time) |
| 🌅 **Two-Format Reports** | Morning briefing for pre-market context; evening analysis with confirmed closing prices and DCA recommendations |
| 🛡️ **3-Gate Safety Filter** | Every BUY signal must pass trend, volatility, and AI news checks before being recommended |
| 📉 **DCA Engine** | Scales into positions gradually up to a daily limit — no lump-sum exposure |
| 📰 **AI News Risk Manager** | Scans up to 5 headlines and summaries per stock (with dates) and blocks recommendations if severe fundamental risks are detected |
| 🔒 **Fail-Secure Architecture** | If the market is closed or an API goes down, the analyst safely skips execution |
| 📱 **Telegram Integration** | Reports pushed straight to your phone, with instant price and news lookup on demand |
| 💬 **Natural Language Control** | Chat to update your portfolio, adjust allocations, change your schedule, or request a price check |
| 🔎 **Auto Ticker Resolution** | Tell the bot a stock name — it resolves the correct T212 and EODHD ticker symbols automatically |

---

## 🛡️ Built-In Security & Protection Layers

- **Isolated & Containerised:** Runs entirely inside a Docker container, completely separated from your host OS. It can only access files within the project folder you explicitly mounted.†
- **No Direct Trade Execution:** The analyst never has access to your trading account password. It uses read-only API permissions and can only provide recommendations — it cannot place trades.
- **Budget-Controlled Running Costs:** All costs are bounded and predictable. OpenRouter charges only what you use — disable auto top-up when registering and set a hard spending limit so there are no surprise bills. EODHD runs on the free tier or a fixed monthly plan. Neither service can charge you more than you authorise.
- **Minimised Prompt Injection Risk (Reports):** During scheduled report generation, the analyst does not browse arbitrary web pages. It exclusively consumes structured financial data from EODHD, significantly reducing the risk of prompt injection attacks via maliciously crafted web content.
- **Reset Without Losing Your Settings:** If anything seems wrong, do not hesitate to use the [Emergency Reset](#-emergency-reset-nuke--restart) procedure to wipe the container and start fresh.

---

## 🛠️ Prerequisites

You only need two things installed before starting:

1. **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** — runs the analyst in its secure container
2. **Telegram** — install on both your phone and your computer:
   - 📱 Mobile: [iOS](https://apps.apple.com/app/telegram-messenger/id686449807) / [Android](https://play.google.com/store/apps/details?id=org.telegram.messenger)
   - 🖥️ Desktop: [Telegram Desktop](https://desktop.telegram.org/) (recommended — makes it much easier to copy pairing codes and API keys during setup)

That's it. The setup script handles all configuration — no code editor required.

---

## 🚀 Quick Start

The setup process is the same on both platforms — the only differences are how you get the files and how you launch the setup script.

---

### Step A — Get the Files

| 🪟 Windows | 🍎 macOS |
|---|---|
| 1. Click the green **Code** button at the top of this page | 1. Click the green **Code** button at the top of this page |
| 2. Select **Download ZIP** | 2. Select **Download ZIP** |
| 3. Right-click the ZIP → **Extract All…** | 3. Double-click the ZIP to extract it |
| 4. Extract to: `C:\Users\YourName\Documents\isa-ai-analyst` | 4. Move the extracted folder to your **Documents** folder |

> **Linux users:** Install [Docker Engine](https://docs.docker.com/engine/install/), extract the ZIP, then run `bash setup.sh`.

---

### Step B — Install Docker Desktop

| 🪟 Windows | 🍎 macOS |
|---|---|
| 1. Download from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) | 1. Download from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) |
| 2. Right-click → **Run as administrator** | 2. Open the `.dmg` and drag Docker to Applications |
| 3. Click **Next** through all defaults | 3. Open Docker from Applications |
| 4. **Restart your PC** when prompted | 4. Approve the system extension if prompted |
| 5. Open **Docker Desktop** from the Start menu and wait for the whale 🐋 icon in the taskbar to stop animating | 5. Wait for the whale 🐋 icon in the menu bar to stop animating |

> ℹ️ **Windows:** Docker automatically installs WSL2 — you do not need to set this up separately.

---

### Step C — Create Your Accounts & Gather API Keys

> *Note: Some links below are affiliate links. Using them helps support continued open-source development at no extra cost to you.*

This step is identical on both platforms. Work through each service in order and keep your keys ready for Step D.

---

#### 🧠 OpenRouter — AI Provider (the Analyst's Brain)

1. Sign up at **[openrouter.ai](https://openrouter.ai)** and verify your email
2. > ⚠️ **Before adding any credit:** go to **Settings → Credits** and make sure **Auto top-up is OFF**. This prevents unexpected charges.
3. Add credit — for a typical portfolio, expect around **US$4–5 per month** of regular usage. Start with US$10–20 to avoid topping up frequently.
4. Go to **Keys** → **Create Key** — name it `ISA AI Analyst`
5. Copy the key

<!-- SCREENSHOT: OpenRouter dashboard showing the Keys page with Create Key button highlighted -->
<img src="docs/screenshots/openrouter-create-key.png" alt="OpenRouter API key creation" width="600" />

> ℹ️ Set a hard **spending limit** in Billing as an extra safeguard against runaway usage.

---

#### 🏦 Trading 212 — Your ISA Broker

1. Sign up: **[Create Trading 212 Account](https://www.trading212.com/invite/4DtCF9r91Ms)**
2. Select **Stocks ISA** and complete identity verification
3. Deposit at least **£1** — the API option won't appear until the account is funded
4. Go to **Settings → API (Beta) → Generate API Key**

   > 🔒 **Critical — set permissions carefully on the next screen:**
   > - ✅ Turn **Account data** → **On**
   > - ✅ Turn **Metadata** → **On** *(required for automatic ticker resolution when adding stocks)*
   > - ✅ Turn **Portfolio** → **On**
   > - Everything else → **Off**
   >
   > Double-check that these two are **Off** before proceeding:
   > - ❌ **Orders — Execute**
   > - ❌ **Pies — Write**
   >
   > ISA AI Analyst only reads your portfolio and market metadata. Leaving execute permissions on means a compromised key could place real trades on your account.

<!-- SCREENSHOT: Trading 212 API permissions screen with Orders-Execute and Pies-Write unchecked -->
<img src="docs/screenshots/t212-api-permissions.png" alt="Trading 212 API permissions — uncheck Orders Execute and Pies Write" width="400" />

5. Copy both the **Key ID** and **Secret Key** immediately — the Secret is shown only once.

---

#### 📊 EODHD — Market Data & Financial News

1. Sign up: **[Create EODHD Account](https://eodhd.com?via=clementha)**
2. Go to your **Dashboard** — your API token is shown at the top
3. Copy the token

<!-- SCREENSHOT: EODHD dashboard showing the API token field highlighted at the top -->
<img src="docs/screenshots/eodhd-api-token.png" alt="EODHD dashboard API token location" width="600" />

> ℹ️ **Free tier limits apply** — see [EODHD Free Tier Limits](#-eodhd-free-tier-limits) for details.

---

#### 💬 Telegram — Your Reporting Interface

> 💡 We recommend doing this step on **Telegram Desktop** — it's much easier to copy tokens and IDs from a computer than a phone screen.

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`, follow the prompts, and copy the **Bot Token**
3. Search for **@userinfobot**, send `/start`, and copy your **Chat ID**

---

### Step D — Run the Setup Script

Make sure **Docker Desktop is open and running**, then launch the setup script:

| 🪟 Windows | 🍎 macOS |
|---|---|
| Navigate to your `Documents\isa-ai-analyst` folder in File Explorer | Open **Terminal** and `cd` to the project folder |
| **Double-click `setup.bat`** | Run `bash setup.sh` |
| *(Or open PowerShell, `cd` to the folder, and run `setup.bat`)* | |

You will see this interactive menu:

```
=================================================
 ISA AI ANALYST - SETUP
=================================================
 Status: [STOPPED / NOT INSTALLED]
-------------------------------------------------
 SETUP CHECKLIST:
  1) [ ]  Set AI API Key (OpenRouter)
  2) [ ]  Set Broker API Keys (Trading 212)
  3) [ ]  Set Market Data API Key (EODHD)
  4) [ ]  Set Telegram API Keys
  5) [ ]  Run Initial Setup  (Complete keys first)
-------------------------------------------------
 CONTROLS:
  6)  Start Agent              (Run Setup first)
  7)  Stop Agent               (Run Setup first)
  8)  View Live Logs           (Run Setup first)
  9)  Approve Telegram Pairing (Agent must be running)
  0)  Exit
=================================================
Enter choice [0-9]:
```

Work through options **1 → 2 → 3 → 4** in order, pasting your API keys when prompted. Once all four are ticked, select **5 (Run Initial Setup)** to boot the container. The status will update to **[RUNNING]** with all items showing **[OK]**.

> 💡 You can return to the setup script at any time to start, stop, view logs, or update your API keys.

---

### Step E — Pair Your Telegram Bot

1. Open Telegram and search for your bot by the username you created with @BotFather
2. Send any message — `hello` is fine
3. The bot replies with a pairing code, for example:
   ```
   Your pairing code is: Z2EDQKMK
   Approve this code to continue.
   ```
4. Go back to the setup script, select option **9 (Approve Telegram Pairing)**, and paste the code when prompted

The bot confirms the connection and is ready.

> ⚠️ You may need to repeat this step if you fully restart the container. See [Troubleshooting](#-troubleshooting) if the code is never accepted.

---

### Step F — Talk to Your Analyst

Open Telegram and message your bot. ISA AI Analyst isn't just a timer that fires off a report twice a day — it's a full conversational AI agent. You can talk to it exactly as you would talk to a real analyst.

#### ⚡ Quick Commands

| Message | What it does |
|---|---|
| `Run it now.` | Triggers an immediate portfolio analysis and report |
| `What's the price of Vodafone?` | Fetches the latest price and news for that stock |
| `Show my portfolio` | Displays current allocations and unallocated percentage |
| `What is my current schedule?` | Shows the configured report times |
| `Add Scottish Mortgage at 25%` | Resolves tickers automatically and adds to your portfolio |
| `Remove Vodafone` | Removes a stock from your portfolio targets |
| `Change Vodafone to 20%` | Adjusts a stock's target allocation |
| `Set my DCA limit to £300` | Updates your daily DCA cap |
| `Set my ISA allowance to £20000` | Updates your total ISA target |
| `Set cash reserve to 20%` | Adjusts the cash buffer percentage |
| `Pause reporting.` | Suspends automatic daily reports |

#### 💬 Ask It Anything — It Thinks Like an Analyst

The command table above barely scratches the surface. Here are some examples of the kinds of conversations you can have:

---

**Research a stock before adding it:**
> *"Can you analyse the recent news for Tesla and tell me if it would pass your risk checks before I officially add it to my portfolio?"*

The analyst fetches live news for any ticker you mention, runs it through the same three safety gates it applies to your existing stocks, and gives you a clear pass/fail with reasoning — in seconds. No need to spend an hour trawling news sites.

---

**Understand the reasoning behind a recommendation:**
> *"Can you explain what a Simple Moving Average is, and why you refuse to buy stocks that are trading below it?"*

You're not expected to just accept the recommendations blindly. Ask it to explain any decision it makes, and it will give you a clear, jargon-free answer. Particularly useful if you're newer to investing and want to build your understanding alongside your portfolio.

---

**Interrogate your own numbers:**
> *"How much of my £20,000 ISA allowance is currently deployed into the market versus sitting in cash?"*

It already knows your portfolio inside out — your allocations, targets, and cash reserve. No spreadsheet, no mental arithmetic. Just ask.

---

**Challenge a signal:**
> *"The report says SELL on Scottish Mortgage — but I think the news is just noise. Walk me through your reasoning."*

The analyst will explain which gate failed and why. You can push back, ask follow-up questions, and make your own call. It's a tool, not an oracle.

---

**Sanity-check a rebalance:**
> *"If I add 15% in Legal & General, what percentage would I have left unallocated across the rest of the portfolio?"*

It'll do the portfolio maths for you instantly and flag if you'd be over-allocating before you commit to anything.

---

### 🎉 Setup Complete!

Congratulations — ISA AI Analyst is now fully up and running!

- ✅ A securely containerised AI analyst running entirely on your own machine
- ✅ Read-only Trading 212 integration — no accidental trades are possible
- ✅ Morning briefing (08:30) and evening analysis (17:30) with 3-gate safety filtering and DCA logic
- ✅ AI-powered financial news risk screening before every recommendation
- ✅ On-demand price and news lookup via Telegram
- ✅ Full natural language portfolio management via Telegram

Your first scheduled report arrives at the next run time (default: 08:30 or 17:30 UK). Can't wait? Send **`Run it now.`** on Telegram for an immediate report.

If you find ISA AI Analyst useful, please consider [⭐ starring the repository](https://github.com/ClementHa/isa-ai-analyst) — it helps others discover the project and keeps development going.

---


## 🍀 Good Luck & Support the Project

Investing is part discipline, part patience — and a little bit of luck never hurts. We hope ISA AI Analyst helps you make more informed, confident decisions with your ISA.

If the analyst has ever kept you from a bad trade, flagged a risk you missed, or simply saved you time — consider buying us a coffee. Every contribution goes directly towards new features, better models, and keeping the project open-source and free.

[![Ko-fi](https://img.shields.io/badge/Support%20on-Ko--fi-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/clementha)

> *"The stock market is a device for transferring money from the impatient to the patient."* — Warren Buffett

Good luck out there. 📈

---

## 📉 EODHD Free Tier Limits

EODHD's free plan includes **20 API calls per day**. Each stock analysis consumes:

- **1 call** per stock for end-of-day price data (used for SMA and volatility calculations)
- **1 call** per stock for financial news headlines

That's **2 calls per stock per report**, or **4 calls per stock per day** across both reports. The free tier comfortably supports:

> 🆓 **Up to 5 stocks across your 2 daily reports** on the free plan.

On-demand price queries (via Telegram) use **2 additional calls** each (1 for live price + 1 for news), so frequent manual lookups will reduce the headroom for stocks. If you want to track more stocks or use price queries heavily, upgrade to a paid EODHD plan. See [EODHD pricing](https://eodhd.com/pricing) for available options.

---

## 🚨 Emergency Reset (Nuke & Restart)

> Use this if the bot behaves unexpectedly, seems stuck in a loop, or you simply want a clean slate.

**Your API keys and portfolio configuration are not affected** — only the running container and its internal state are wiped.

**Step 1 — Stop and remove everything:**

```bash
docker compose down --volumes --rmi all
```

**Step 2 — Rebuild and restart fresh:**

```bash
docker compose up -d --build
```

On Windows you can alternatively re-run `setup.bat` and select option **5 (Run Initial Setup)**.

**Step 3 — Re-pair your Telegram bot:**

The pairing state is reset — redo [Step E](#step-e--pair-your-telegram-bot) once more.

> ℹ️ To preserve conversation history and learned preferences instead, use `docker compose stop` followed by `docker compose start` — these pause and resume without wiping state.

---

## 🩺 Troubleshooting

**Pairing code is never accepted**
- The container session state was likely lost on a restart
- Fix: `docker compose down` → `docker compose up -d` → redo Step E

**Bot not responding on Telegram**
- Confirm Docker is running: `docker compose ps`
- Check logs via the setup script (option 8) or `docker compose logs -f`
- Confirm you completed Step E — the bot silently ignores all messages until paired
- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are correct (re-run option 4 in the setup script)

**"API Key invalid" error in logs**
- Re-run the relevant step in the setup script and re-paste the key
- Check your EODHD subscription is active
- Confirm both `T212_KEY_ID` and `T212_SECRET` are filled — both are required
- If your T212 key stopped working, verify your ISA account still has funds

**Reports not arriving at scheduled times**
- Check your Docker host's system clock and timezone are correct
- Test immediately with `Run it now.` in Telegram

**Docker Desktop won't start on Windows**
- Restart your PC if you haven't since the Docker installation — Docker handles WSL2 automatically
- If you still see a WSL error, open PowerShell as Administrator and run `wsl --install`, then restart

**`setup.bat` closes immediately on Windows**
- Right-click `setup.bat` → **Run as Administrator**, or open a Command Prompt first and run `setup.bat` from within it so the window stays open on error

---

## 🔭 Roadmap

### 📊 Back-Testing

If ISA AI Analyst receives strong community feedback, the next major feature planned is **back-testing capability**.

Back-testing lets you run the analyst's strategy against **historical market data** to see how its recommendations would have performed in the past — before risking any real capital. The benefits include:

- **Validate the strategy** — see win/loss ratios, average returns, and drawdown periods on real historical data
- **Tune your parameters** — experiment with different DCA limits, volatility thresholds, and news sensitivity settings and compare outcomes
- **Build confidence** — understand how the analyst would have behaved during specific market events (e.g. a sector crash, a spike in volatility)

---

### ☁️ Managed Cloud Service

One of the biggest practical limitations of the self-hosted version is that **it only runs when your computer is on**. If your machine is asleep at 08:30, you miss the morning report.

A managed cloud version is planned to solve this. The goal is simple: sign up, connect your API keys via a secure web dashboard, and your analyst runs 24/7 in the cloud — no Docker, no installation, no leaving your desktop powered on.

**Planned pricing: £5/month** — enough to cover hosting costs while keeping it genuinely affordable for any ISA investor.

> 🙋 **Interested?** Star the repo and leave a comment in [Discussions](https://github.com/ClementHa/isa-ai-analyst/discussions) — demand directly influences how soon this gets built.

---

## 🤝 Contributing

Contributions are welcome and appreciated! Whether it's a bug fix, a new feature, or an improvement to the documentation — please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a Pull Request. It covers how to fork the repo, branch naming conventions, how to run the project locally for development, and the PR review process.

If you have an idea but aren't sure where to start, open a [GitHub Discussion](https://github.com/ClementHa/isa-ai-analyst/discussions) first — happy to talk it through.

---

## 📝 License

This project is open-source under the [MIT License](LICENSE).

---

## ⚠️ Disclaimer

This software is provided for **educational and informational purposes only**. It does not constitute financial advice. The AI can hallucinate, and market data APIs can return incorrect or delayed data. **Always verify recommendations manually before taking any action.** Never risk capital you cannot afford to lose. Past performance is not indicative of future results.

---

† No Docker container is a perfect security boundary. Containers share the host's network stack by default, meaning a severely compromised container could theoretically attempt to probe your host machine over the local Docker bridge network. ISA AI Analyst does not mount the Docker socket and does not run in privileged mode, which significantly limits the blast radius of any such attack. For the vast majority of users, the container isolation is more than sufficient — but it is not equivalent to a fully separate virtual machine.

