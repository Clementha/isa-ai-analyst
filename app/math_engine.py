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
        # Add this new line to pull the £20k target:
        ISA_ALLOWANCE = config.get("isa_allowance_target", 20000) 
except Exception as e:
    print(f"❌ Failed to load {CONFIG_PATH}. Error: {e}")
    TARGET_WEIGHTS = {}
    TARGET_CASH_PCT = 0.25
    ISA_ALLOWANCE = 20000

# --- DATA FETCHING ---
def fetch_eodhd_data(symbol):
    url = f"https://eodhd.com/api/eod/{symbol}?api_token={EODHD_API_KEY}&fmt=json&period=d"
    try:
        return requests.get(url).json()[-20:]
    except:
        return []

def fetch_news(symbol):
    url = f"https://eodhd.com/api/news?api_token={EODHD_API_KEY}&s={symbol}&limit=3"
    try:
        news = requests.get(url).json()
        # Clean up the ugly HTML entities before saving them
        return [html.unescape(article['title']) for article in news]
    except:
        return ["No recent news found."]

def analyse_news_with_AI_model(symbol, news_list):
    # If there is no news, skip the AI completely
    if not news_list or "No recent news found" in news_list[0]:
        return "NO_NEWS"
        
    # STRICT CHECK: Fail loudly if the user forgot their config
    if not LLM_API_KEY or not LLM_BASE_URL:
        print(f"⚠️ CONFIG ERROR: Missing LLM_API_KEY or LLM_BASE_URL in .env for {symbol}.")
        return "ERROR"
        
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"You are a strict quantitative risk manager. Review these recent headlines for {symbol}. If they contain severe fundamental risks (fraud, lawsuits, bankruptcy, major downgrades), reply with the exact word 'FAIL'. If they are neutral, positive, or standard market noise, reply with the exact word 'PASS'.\n\nHeadlines:\n" + "\n".join(news_list)
    
    payload = {
        "model": LLM_MODEL, 
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0, 
        "max_tokens": 10
    }
    
    try:
        # Added a 10-second timeout so a dead API doesn't freeze your bot forever
        resp = requests.post(LLM_BASE_URL, headers=headers, json=payload, timeout=10)
        resp.raise_for_status() # Automatically triggers the Except block if the API returns a 400/500 error
        
        content = resp.json()['choices'][0]['message']['content'].strip().upper()
        return "FAIL" if "FAIL" in content else "PASS"
    except Exception as e:
        print(f"❌ LLM API Error for {symbol}: {e}")
        return "ERROR"


def fetch_t212_portfolio():
    headers = {"Authorization": T212_AUTH_HEADER}
    try:
        # Fetch actual cash and positions from Trading 212
        cash_resp = requests.get("https://live.trading212.com/api/v0/equity/account/cash", headers=headers).json()
        pos_resp = requests.get("https://live.trading212.com/api/v0/equity/portfolio", headers=headers).json()
        
        # Check if the API rejected our keys
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

# 1. Create a massive string to hold the entire report instead of just printing it
report_content = "=== 📊 DAILY PORTFOLIO REPORT ===\n\n"
report_content += f"Total Value: £{total_value:.2f}\n"
report_content += f"Target Cash: {TARGET_CASH_PCT * 100:.1f}%\n\n"
report_content += "-" * 30 + "\n\n"

for symbol, target_pct in TARGET_WEIGHTS.items():
    base_ticker = symbol.split('.')[0] 
    current_value = next((val for t212_ticker, val in current_positions.items() if base_ticker in t212_ticker), 0)
    
    current_pct = (current_value / total_value) * 100 if total_value > 0 else 0
    target_value = ISA_ALLOWANCE * target_pct
    delta_value = target_value - current_value

    data = fetch_eodhd_data(symbol)
    if not data or len(data) < 20:
        continue
        
    closes = [float(day['close']) for day in data]
    latest = closes[-1]
    prev = closes[-2]
    
    # Fetch the news immediately so we can grade it
    recent_news = fetch_news(symbol)
    if not recent_news:
        recent_news = ["No recent news found."]
    
    # --- 1. EVALUATE THE 3 GATES ---
    sma_pass = latest > statistics.mean(closes)
    vol_pass = abs((latest - prev) / prev) * 100 < 5.0
    
    # Let the AI model read the news
    news_sentiment = analyse_news_with_AI_model(symbol, recent_news)
    
    if news_sentiment == "NO_NEWS":
        news_pass = True  # Don't block a trade just because it's quiet
        news_icon = "🤷‍♂️"
    elif news_sentiment == "FAIL":
        news_pass = False
        news_icon = "👎"
    elif news_sentiment == "ERROR":
        news_pass = False # FAIL-SECURE: Block the trade if the AI is broken/misconfigured
        news_icon = "⚠️"
    else:
        news_pass = True
        news_icon = "👍"
    
    # --- 2. GENERATE TRADING SIGNAL ---
    # Now requires ALL THREE gates to pass
    if sma_pass and vol_pass and news_pass:
        signal_color = "🟢 GREEN" 
        if delta_value > 50:
            action = f"BUY £{delta_value:.2f}"
        else:
            action = "HOLD (Near target)"
    else:
        signal_color = "🔴 RED" 
        if current_value > 0:
            action = f"SELL ALL £{current_value:.2f}"
        else:
            action = "AVOID"

    # --- 3. FORMAT THE ICONS ---
    sma_icon = "👍" if sma_pass else "👎"
    vol_icon = "👍" if vol_pass else "👎"

    # --- 4. BUILD THE REPORT TEXT ---
    report_content += f"🔹 <b>{symbol}</b> | Price: {latest:.2f}\n"
    report_content += f"Target: {target_pct*100:.0f}% (£{target_value:.2f}) | Current: {current_pct:.1f}% (£{current_value:.2f})\n"
    report_content += f"Signal: {signal_color} [{action}]\n"
    report_content += f"Gates: SMA {sma_icon} | News {news_icon} | Volatility {vol_icon}\n"
    
    report_content += "Catalysts:\n"
    for item in recent_news:
        report_content += f" - {item}\n"
    report_content += "\n" # Spacer

# --- ADD THE LEAN DISCLAIMER ---
disclaimer_text = """---
⚠️ <b>DISCLAIMER:</b> This report is AI-generated and may contain errors or hallucinations. Always verify financial data and news with official sources before trading. Never share sensitive data or passwords in this chat.
"""
report_content += disclaimer_text
# -------------------------------

# 2. Print it to the terminal so you can still see it when testing
print(report_content)

# 3. SAVE IT TO THE HARD DRIVE FOR THE AI TO READ
output_path = '/app/portfolio.md'

try:
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(report_content)
    print(f"✅ Successfully saved report to: {output_path}")
except Exception as e:
    print(f"❌ Failed to save file: {e}")

    # --- BYPASS OPENCLAW: SEND DIRECTLY TO TELEGRAM ---


# Only attempt to send if the keys were successfully found in the .env file
if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # We use json=payload instead of data=payload to ensure the formatting stays clean
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": report_content,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(telegram_url, json=payload)
        
        # Check if Telegram accepted the message
        if response.status_code == 200:
            print("✅ Successfully pushed report directly to Telegram!")
        else:
            print(f"❌ Telegram rejected the message: {response.text}")
            
    except Exception as e:
        print(f"❌ Failed to connect to Telegram: {e}")
else:
    print("⚠️ Skipping Telegram push: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not found in .env.")