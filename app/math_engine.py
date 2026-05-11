# Copyright (c) 2026 Clement Ha
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
import requests
import statistics
import base64
import os
import json
import html
import datetime
import sys

# 🛑 WEEKEND CHECK: 0=Mon, 1=Tue, ..., 5=Sat, 6=Sun
if datetime.datetime.now().weekday() >= 5:
    print("🛑 Weekend detected. LSE Market is closed. Exiting.")
    sys.exit(0)

# Session mode: passed from scheduler ("morning"/"evening"), or auto-detected by time of day.
# Anything before 14:00 = morning briefing; 14:00+ = evening analysis.
SESSION = sys.argv[1] if len(sys.argv) > 1 else ("evening" if datetime.datetime.now().hour >= 14 else "morning")

# --- Helper function to manually read the .env file ---
def get_secret(key):
    val = os.getenv(key)
    if val:
        return val
    try:
        with open('/app/.env', 'r') as f:
            for line in f:
                if line.startswith(key + '='):
                    return line.split('=', 1)[1].strip()
    except Exception:
        pass
    return None

# --- SECURE API KEYS ---
EODHD_API_KEY = get_secret("EODHD_API_KEY")
T212_KEY_ID = get_secret("T212_KEY_ID")
T212_SECRET = get_secret("T212_SECRET")
TELEGRAM_TOKEN = get_secret("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = get_secret("TELEGRAM_CHAT_ID")
LLM_API_KEY = get_secret("LLM_API_KEY")
LLM_BASE_URL = get_secret("LLM_BASE_URL")
LLM_MODEL = get_secret("LLM_MODEL")

# Create the secure Base64 Basic Auth token for Trading 212
t212_credentials = f"{T212_KEY_ID}:{T212_SECRET}"
encoded_credentials = base64.b64encode(t212_credentials.encode('utf-8')).decode('utf-8')
T212_AUTH_HEADER = f"Basic {encoded_credentials}"

# --- LOAD PORTFOLIO CONFIGURATION ---
CONFIG_PATH = '/app/portfolio_targets.json'
try:
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
        TARGET_WEIGHTS = config.get("holdings", {})
        TARGET_CASH_PCT = config.get("target_cash_pct", 0.25)
        ISA_ALLOWANCE = config.get("isa_allowance_target", 20000)
        DAILY_DCA_LIMIT = config.get("daily_dca_limit", 500)
except Exception as e:
    print(f"❌ Failed to load {CONFIG_PATH}. Error: {e}")
    TARGET_WEIGHTS = {}
    TARGET_CASH_PCT = 0.25
    ISA_ALLOWANCE = 20000
    DAILY_DCA_LIMIT = 500

# --- DATA FETCHING ---
def fetch_eodhd_data(symbol):
    url = f"https://eodhd.com/api/eod/{symbol}?api_token={EODHD_API_KEY}&fmt=json&period=d"
    try:
        return requests.get(url).json()[-20:]
    except:
        return []

def fetch_news(symbol):
    url = f"https://eodhd.com/api/news?api_token={EODHD_API_KEY}&s={symbol}&limit=5"
    try:
        news = requests.get(url).json()
        items = []
        for article in news:
            raw_date = article.get('date', '')
            try:
                date_str = datetime.datetime.fromisoformat(raw_date.replace('Z', '+00:00')).strftime('%d %b')
            except Exception:
                date_str = raw_date[:10] if raw_date else '?'
            items.append({
                "date": date_str,
                "title": html.unescape(article.get('title', '')),
                "summary": html.unescape(article.get('content', '') or '')
            })
        return items
    except:
        return []

def fetch_realtime_price(symbol):
    url = f"https://eodhd.com/api/real-time/{symbol}?api_token={EODHD_API_KEY}&fmt=json"
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if isinstance(data, dict) and isinstance(data.get('close'), (int, float)):
            return data
        return None  # Free plan — endpoint not available
    except:
        return None

def analyse_news_with_AI_model(name, news_items):
    if not news_items:
        return "NO_NEWS"

    if not LLM_API_KEY or not LLM_BASE_URL:
        print(f"⚠️ CONFIG ERROR: Missing LLM_API_KEY or LLM_BASE_URL in .env for {name}.")
        return "ERROR"

    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }

    formatted_news = "\n".join(
        f"[{item['date']}] {item['title']}" + (f"\n  {item['summary']}" if item['summary'] else "")
        for item in news_items
    )

    prompt = (
        f"You are a strict quantitative risk manager for a capital-preservation-first ISA portfolio. "
        f"Review these recent news items for {name} (a UK-listed equity). "
        f"Reply with the exact word 'FAIL' only if the news indicates severe fundamental risks such as "
        f"fraud, criminal investigations, bankruptcy, insolvency, major credit downgrades, or regulatory sanctions. "
        f"Sector-wide macroeconomic concerns, routine earnings misses, or analyst target price changes do NOT warrant FAIL. "
        f"Reply with the exact word 'PASS' for all other cases.\n\nNews items:\n"
        + formatted_news
    )

    actual_model = (LLM_MODEL or "").replace("openrouter/", "")
    payload = {
        "model": actual_model,
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        resp = requests.post(LLM_BASE_URL, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        content = resp.json()['choices'][0]['message']['content'].strip().upper()
        return "FAIL" if "FAIL" in content else "PASS"
    except Exception as e:
        print(f"❌ LLM API Error for {name}: {e}")
        return "ERROR"

def fetch_t212_portfolio():
    headers = {"Authorization": T212_AUTH_HEADER}
    try:
        cash_resp = requests.get("https://live.trading212.com/api/v0/equity/account/cash", headers=headers).json()
        pos_resp = requests.get("https://live.trading212.com/api/v0/equity/portfolio", headers=headers).json()

        if 'code' in cash_resp and cash_resp['code'] == 'AuthenticationFailed':
            print("Trading 212 Auth Failed. Check your Key ID and Secret.")
            return 0, {}

        total_cash = cash_resp.get('total', 0)
        portfolio = {pos['ticker']: pos['currentValue'] for pos in pos_resp}
        total_invested = sum(portfolio.values())

        return total_cash + total_invested, portfolio
    except Exception as e:
        print(f"Error connecting to Trading 212: {e}")
        return 0, {}

# --- THE MATH ENGINE ---
total_value, current_positions = fetch_t212_portfolio()
today_str = datetime.datetime.now().strftime("%d %b %Y")

if SESSION == "morning":
    report_content = f"=== 🌅 MORNING BRIEFING ===\n"
    report_content += f"{today_str} | Prices as of previous close\n\n"
    report_content += f"Portfolio Value: £{total_value:.2f}\n"
    report_content += "-" * 30 + "\n\n"
else:
    report_content = f"=== 📊 EVENING ANALYSIS ===\n"
    report_content += f"{today_str} | Today's closing prices\n\n"
    report_content += f"Total Value: £{total_value:.2f}\n"
    report_content += f"Target Cash: {TARGET_CASH_PCT * 100:.1f}%\n\n"
    report_content += "-" * 30 + "\n\n"

for t212_ticker, stock_data in TARGET_WEIGHTS.items():
    target_pct = stock_data.get("target_weight", 0)
    eodhd_ticker = stock_data.get("eodhd_ticker", "")
    name = stock_data.get("name", t212_ticker)

    current_value = current_positions.get(t212_ticker, 0)
    current_pct = (current_value / total_value) * 100 if total_value > 0 else 0
    target_value = ISA_ALLOWANCE * target_pct
    delta_value = target_value - current_value

    data = fetch_eodhd_data(eodhd_ticker)
    if not data or len(data) < 20:
        report_content += f"🔹 <b>{name} ({t212_ticker} / {eodhd_ticker})</b>\n"
        report_content += "Signal: ⚠️ ERROR [Insufficient EODHD Data / Bad Ticker]\n\n"
        continue

    closes = [float(day['close']) for day in data]
    latest = closes[-1]
    prev = closes[-2]

    raw_date = data[-1].get('date', '')
    try:
        price_date = datetime.datetime.strptime(raw_date, '%Y-%m-%d').strftime('%a %d %b')
    except ValueError:
        price_date = raw_date

    recent_news = fetch_news(eodhd_ticker)

    # --- EVALUATE THE 3 GATES ---
    sma_pass = latest > statistics.mean(closes)
    vol_pass = abs((latest - prev) / prev) * 100 < 5.0
    news_sentiment = analyse_news_with_AI_model(name, recent_news)

    if news_sentiment == "NO_NEWS":
        news_pass = True
        news_icon = "🤷‍♂️"
    elif news_sentiment == "FAIL":
        news_pass = False
        news_icon = "👎"
    elif news_sentiment == "ERROR":
        news_pass = False
        news_icon = "⚠️"
    else:
        news_pass = True
        news_icon = "👍"

    sma_icon = "👍" if sma_pass else "👎"
    vol_icon = "👍" if vol_pass else "👎"
    all_green = sma_pass and vol_pass and news_pass

    if SESSION == "morning":
        report_content += f"🔹 <b>{name} ({t212_ticker} / {eodhd_ticker})</b> | Close: £{latest:.2f} ({price_date})\n"
        report_content += f"Holding: {current_pct:.1f}% (£{current_value:.2f}) → Target: {target_pct*100:.0f}%\n"
        report_content += f"Gates: SMA {sma_icon} | Vol {vol_icon} | News {news_icon}\n"
        report_content += f"Outlook: {'🟢 GREEN' if all_green else '🔴 RISK FLAGGED'}\n"
        report_content += "Overnight News:\n"
    else:
        if all_green:
            signal_color = "🟢 GREEN"
            if delta_value > 50:
                buy_amount = min(delta_value, DAILY_DCA_LIMIT)
                action = f"BUY £{buy_amount:.2f} (DCA mode, £{delta_value:.2f} total gap)" if buy_amount < delta_value else f"BUY £{buy_amount:.2f}"
            else:
                action = "HOLD (Near target)"
        else:
            signal_color = "🔴 RED"
            action = f"SELL ALL £{current_value:.2f}" if current_value > 0 else "AVOID"

        report_content += f"🔹 <b>{name} ({t212_ticker} / {eodhd_ticker})</b> | Close: £{latest:.2f} ({price_date})\n"
        report_content += f"Target: {target_pct*100:.0f}% (£{target_value:.2f}) | Current: {current_pct:.1f}% (£{current_value:.2f})\n"
        report_content += f"Signal: {signal_color} [{action}]\n"
        report_content += f"Gates: SMA {sma_icon} | Vol {vol_icon} | News {news_icon}\n"
        report_content += "Today's News:\n"

    if recent_news:
        for item in recent_news:
            report_content += f" - [{item['date']}] {html.escape(item['title'])}\n"
    else:
        report_content += " - No recent news found.\n"
    report_content += "\n"

disclaimer_text = "\n<i>* Disclaimer: This AI-generated report may contain errors. Verify data independently before trading.</i>"
report_content += disclaimer_text

print(report_content)

output_path = '/app/portfolio.md'
try:
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(report_content)
    print(f"✅ Successfully saved report to: {output_path}")
except Exception as e:
    print(f"❌ Failed to save file: {e}")

if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": report_content,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(telegram_url, json=payload)
        if response.status_code == 200:
            print("✅ Successfully pushed report directly to Telegram!")
        else:
            print(f"❌ Telegram rejected the message: {response.text}")
    except Exception as e:
        print(f"❌ Failed to connect to Telegram: {e}")
else:
    print("⚠️ Skipping Telegram push: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not found in .env.")
