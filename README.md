# 📈 IsaInvestClaw 

IsaInvestClaw is an autonomous, AI-powered quantitative trading engine built specifically for UK Tax-Free ISA accounts. Powered by the OpenClaw framework, it runs locally, fetches daily market data, grades financial news, and delivers strict, conservative portfolio adjustments directly to your Telegram.

**Capital preservation is the primary directive.**

## ⚙️ Features
* **100% Autonomous:** Runs automatically at UK Market hours (08:30 & 16:00 LSE time).
* **AI News Risk Manager:** Uses LLMs to scan daily headlines and block trades if severe fundamental risks (fraud, lawsuits) are detected.
* **Fail-Secure Architecture:** If the market is closed (weekends) or an API goes down, the bot safely skips execution.
* **Telegram Integration:** Get beautiful, actionable Markdown reports pushed straight to your phone.

---

## 🛠️ Prerequisites & Recommended Tools

To run this bot, you will need a few standard API keys. 
*(Note: Some of the links below are affiliate links. Using them helps support the continued open-source development of IsaInvestClaw at no extra cost to you!)*

1. **Brokerage Account:** [Trading 212](https://www.trading212.com/invite/4DtCF9r91Ms) (Free UK ISA with API access)
2. **Market Data API:** [EODHD APIs](https://eodhd.com?via=clementha) (For end-of-day pricing and financial news)
3. **AI Provider:** [Novita API](https://novita.ai/?ref=zmyynju&utm_source=affiliate) (For the "Brain" of the Bot)

---

## 🚀 Quick Start Installation

**1. Clone the repository:**
```bash
git clone [https://github.com/yourusername/IsaInvestClaw.git](https://github.com/yourusername/IsaInvestClaw.git)
cd IsaInvestClaw
```

**2. Configure your secrets:**
Copy the `.env.example` file and rename it to `.env`. Fill in your API keys. 
> 🔒 **SECURITY NOTE:** Never send your API keys to the bot via Telegram chat. ALWAYS put your API keys directly into this local `.env` file. 

**3. Set your Portfolio:**
Copy `config/portfolio_targets.example.json` to `app/portfolio_targets.json` and adjust your target weights and ISA allowance.

**4. Launch the Engine:**
```bash
docker compose up -d
```

**5. Talk to your Bot:**
Message your bot on Telegram: *"What is my current schedule?"* By default, it runs at 08:30 and 16:00 UK time. To trigger a manual test report, just text it: *"Run it now."*

---

## 📝 License
This project is open-source and available under the [MIT License](LICENSE).

⚠️ **Disclaimer:** This software is for educational purposes only. Do not risk money you cannot afford to lose. The AI can hallucinate, and market data APIs can be wrong. Always verify trades manually.