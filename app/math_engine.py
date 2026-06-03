# Copyright (c) 2026 Clement Ha
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
import requests
import base64
import json
import html
import datetime
import sys
from lib import get_secret, fetch_eod_data, fetch_news, evaluate_gates, EODHD_API_KEY, T212_BASE, T212_MODE

# Session mode: passed from scheduler ("morning"/"evening"), or auto-detected by time of day.
# Anything before 14:00 = morning briefing; 14:00+ = evening analysis.
SESSION = sys.argv[1] if len(sys.argv) > 1 else ("evening" if datetime.datetime.now().hour >= 14 else "morning")

# --- SECURE API KEYS ---
T212_KEY_ID = get_secret("T212_KEY_ID")
T212_SECRET = get_secret("T212_SECRET")
TELEGRAM_TOKEN = get_secret("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = get_secret("TELEGRAM_CHAT_ID")

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

def fetch_t212_portfolio():
    headers = {"Authorization": T212_AUTH_HEADER}
    try:
        cash_r = requests.get(f"{T212_BASE}/equity/account/cash", headers=headers)
        if cash_r.status_code == 401:
            hint = " Practice key used with T212_MODE=live, or live key used with T212_MODE=practice?" if T212_MODE == 'practice' else " Check your T212_KEY_ID and T212_SECRET."
            print(f"Trading 212 Auth Failed (401).{hint}")
            return 0, {}
        cash_resp = cash_r.json()
        if 'code' in cash_resp and cash_resp['code'] == 'AuthenticationFailed':
            hint = " Practice key used with T212_MODE=live, or live key used with T212_MODE=practice?" if T212_MODE == 'practice' else " Check your T212_KEY_ID and T212_SECRET."
            print(f"Trading 212 Auth Failed.{hint}")
            return 0, {}

        pos_resp = requests.get(f"{T212_BASE}/equity/portfolio", headers=headers).json()

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

mode_badge = "🧪 PRACTICE" if T212_MODE == "practice" else "🏦 LIVE"

if SESSION == "morning":
    report_content = f"=== 🌅 MORNING BRIEFING ===\n"
    report_content += f"{today_str} | {mode_badge} | Prices as of previous close\n\n"
    report_content += f"Portfolio Value: £{total_value:.2f}\n"
    report_content += "-" * 30 + "\n\n"
else:
    report_content = f"=== 📊 EVENING ANALYSIS ===\n"
    report_content += f"{today_str} | {mode_badge} | Today's closing prices\n\n"
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

    data = fetch_eod_data(eodhd_ticker)
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
    gates = evaluate_gates(closes, recent_news, name)

    if SESSION == "morning":
        report_content += f"🔹 <b>{name} ({t212_ticker} / {eodhd_ticker})</b> | Close: £{latest:.2f} ({price_date})\n"
        report_content += f"Holding: {current_pct:.1f}% (£{current_value:.2f}) → Target: {target_pct*100:.0f}%\n"
        report_content += f"Gates: SMA {gates['sma_icon']} | Vol {gates['vol_icon']} | News {gates['news_icon']}\n"
        if gates['news_reason']:
            report_content += f"News: {html.escape(gates['news_reason'])}\n"
        report_content += f"Outlook: {'🟢 GREEN' if gates['all_green'] else '🔴 RISK FLAGGED'}\n"
        news_label = "Overnight News"
    else:
        if gates['all_green']:
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
        report_content += f"Gates: SMA {gates['sma_icon']} | Vol {gates['vol_icon']} | News {gates['news_icon']}\n"
        if gates['news_reason']:
            report_content += f"News: {html.escape(gates['news_reason'])}\n"
        news_label = "Today's News"

    if recent_news is None:
        report_content += f"{news_label}:\n - ⚠️ News fetch failed (API error or quota exceeded).\n"
    elif len(recent_news) == 0:
        report_content += f"{news_label}:\n - No recent news found.\n"
    else:
        news_lines = []
        for i, item in enumerate(recent_news):
            prefix = "⚠️ " if i in gates['news_guilty'] else ""
            news_lines.append(f" - {prefix}[{item['date']}] {html.escape(item['title'])}")
        news_text = "\n".join(news_lines)
        report_content += f"{news_label}:\n<blockquote expandable>{news_text}</blockquote>\n"
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
