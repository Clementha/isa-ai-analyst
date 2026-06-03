# Copyright (c) 2026 Clement Ha
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
import os
import html
import datetime
import statistics
import requests

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

T212_MODE = (get_secret("T212_MODE") or "live").lower()
T212_BASE = f"https://{'demo' if T212_MODE == 'practice' else 'live'}.trading212.com/api/v0"

def search_eodhd(query):
    url = f"https://eodhd.com/api/search/{query}?api_token={EODHD_API_KEY}&fmt=json"
    try:
        resp = requests.get(url, timeout=10)
        return resp.json() if resp.status_code == 200 else []
    except Exception:
        return []

def fetch_eod_data(symbol):
    url = f"https://eodhd.com/api/eod/{symbol}?api_token={EODHD_API_KEY}&fmt=json&period=d"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        return data[-20:] if isinstance(data, list) and len(data) > 0 else []
    except Exception:
        return []

def fetch_news(symbol):
    url = f"https://eodhd.com/api/news?api_token={EODHD_API_KEY}&s={symbol}&limit=5&fmt=json"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"⚠️ EODHD news error for {symbol}: HTTP {resp.status_code} — {resp.text[:100]}")
            return None  # API error — distinct from genuine no-news
        news = resp.json()
        if not isinstance(news, list):
            print(f"⚠️ EODHD news unexpected response for {symbol}: {str(news)[:100]}")
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
        return items  # [] means genuinely no news, None means error
    except Exception as e:
        print(f"⚠️ EODHD news exception for {symbol}: {e}")
        return None

def analyse_news(name, news_items):
    if news_items is None:
        return "ERROR"
    if len(news_items) == 0:
        return "NO_NEWS"
    if not LLM_API_KEY or not LLM_BASE_URL:
        print(f"⚠️ CONFIG ERROR: Missing LLM_API_KEY or LLM_BASE_URL for {name}.")
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
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0
    }

    try:
        headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}
        resp = requests.post(LLM_BASE_URL, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        content = resp.json()['choices'][0]['message']['content'].strip().upper()
        return "FAIL" if "FAIL" in content else "PASS"
    except Exception as e:
        print(f"❌ LLM API Error for {name}: {e}")
        return "ERROR"

def evaluate_gates(closes, news_items, name):
    """Evaluate all 3 safety gates. Returns dict with pass/fail booleans and display icons."""
    sma_pass = closes[-1] > statistics.mean(closes)
    vol_pass = abs((closes[-1] - closes[-2]) / closes[-2]) * 100 < 5.0
    sentiment = analyse_news(name, news_items)

    if sentiment == "NO_NEWS":
        news_pass, news_icon = True, "🤷‍♂️"
    elif sentiment == "FAIL":
        news_pass, news_icon = False, "👎"
    elif sentiment == "ERROR":
        news_pass, news_icon = False, "⚠️"
    else:
        news_pass, news_icon = True, "👍"

    return {
        "sma_pass": sma_pass,
        "vol_pass": vol_pass,
        "news_pass": news_pass,
        "sma_icon": "👍" if sma_pass else "👎",
        "vol_icon": "👍" if vol_pass else "👎",
        "news_icon": news_icon,
        "all_green": sma_pass and vol_pass and news_pass,
    }
