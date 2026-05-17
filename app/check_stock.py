# Copyright (c) 2026 Clement Ha
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# Usage: python3 /app/check_stock.py "BAE Systems"
#    or: python3 /app/check_stock.py "BA.LSE"
import sys
import requests
import statistics
import html
import datetime
import os

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

EODHD_API_KEY = get_secret("EODHD_API_KEY")
LLM_API_KEY = get_secret("LLM_API_KEY")
LLM_BASE_URL = get_secret("LLM_BASE_URL")
LLM_MODEL = get_secret("LLM_MODEL")

def search_eodhd(query):
    url = f"https://eodhd.com/api/search/{query}?api_token={EODHD_API_KEY}&fmt=json"
    try:
        resp = requests.get(url, timeout=10)
        return resp.json() if resp.status_code == 200 else []
    except Exception:
        return []

def fetch_eod_data(ticker):
    url = f"https://eodhd.com/api/eod/{ticker}?api_token={EODHD_API_KEY}&fmt=json&period=d"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        return data[-20:] if isinstance(data, list) and len(data) > 0 else []
    except Exception:
        return []

def fetch_news(ticker):
    url = f"https://eodhd.com/api/news?api_token={EODHD_API_KEY}&s={ticker}&limit=5&fmt=json"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None
        news = resp.json()
        if not isinstance(news, list):
            return None
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
    except Exception:
        return None

def analyse_news(name, news_items):
    if news_items is None:
        return "ERROR"
    if len(news_items) == 0:
        return "NO_NEWS"
    if not LLM_API_KEY or not LLM_BASE_URL:
        return "ERROR"

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
        headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}
        resp = requests.post(LLM_BASE_URL, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        content = resp.json()['choices'][0]['message']['content'].strip().upper()
        return "FAIL" if "FAIL" in content else "PASS"
    except Exception:
        return "ERROR"

def main():
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    if not query:
        print("Usage: python3 /app/check_stock.py <stock name or EODHD ticker>")
        sys.exit(1)

    # Resolve ticker — accept direct EODHD format (e.g. BA.LSE) or search by name
    if '.' in query and len(query.split('.')) == 2 and ' ' not in query:
        eodhd_ticker = query.upper()
        name = eodhd_ticker
    else:
        results = search_eodhd(query)
        if not results:
            print(f"No EODHD results found for '{query}'. Check the name or try the ticker directly.")
            sys.exit(1)
        lse = [r for r in results if r.get('Exchange') == 'LSE']
        match = lse[0] if lse else results[0]
        code = match.get('Code', '')
        exchange = match.get('Exchange', '')
        name = match.get('Name', query)
        eodhd_ticker = f"{code}.{exchange}"

    # Fetch price data
    data = fetch_eod_data(eodhd_ticker)
    if not data or len(data) < 2:
        print(f"ERROR: Insufficient price data for {eodhd_ticker}. Check the ticker or EODHD daily quota.")
        sys.exit(1)

    closes = [float(day['close']) for day in data]
    latest = closes[-1]
    prev = closes[-2]
    raw_date = data[-1].get('date', '')
    try:
        price_date = datetime.datetime.strptime(raw_date, '%Y-%m-%d').strftime('%a %d %b')
    except Exception:
        price_date = raw_date

    news = fetch_news(eodhd_ticker)

    sma_pass = latest > statistics.mean(closes)
    vol_pass = abs((latest - prev) / prev) * 100 < 5.0
    sentiment = analyse_news(name, news)

    sma_icon = "👍" if sma_pass else "👎"
    vol_icon = "👍" if vol_pass else "👎"

    if sentiment == "NO_NEWS":
        news_pass = True
        news_icon = "🤷‍♂️"
    elif sentiment == "FAIL":
        news_pass = False
        news_icon = "👎"
    elif sentiment == "ERROR":
        news_pass = False
        news_icon = "⚠️"
    else:
        news_pass = True
        news_icon = "👍"

    all_green = sma_pass and vol_pass and news_pass

    print(f"{name} ({eodhd_ticker}): £{latest:.4f} (as of {price_date})")
    print(f"SMA {sma_icon} | Vol {vol_icon} | News {news_icon}")
    if all_green:
        print("Overall: 🟢 GREEN — would qualify for a BUY signal")
    else:
        print("Overall: 🔴 RED — would not qualify")

if __name__ == "__main__":
    main()
