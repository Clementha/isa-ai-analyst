# Copyright (c) 2026 Clement Ha
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
import os
import re
import html
import base64
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
    from_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
    url = f"https://eodhd.com/api/news?api_token={EODHD_API_KEY}&s={symbol}&limit=10&from={from_date}&fmt=json"
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

def eodhd_ticker_from_t212(t212_ticker):
    """Derive an EODHD LSE ticker from a T212 ticker. Handles both CODE_LSE_EQ
    (equities, e.g. GSK_LSE_EQ -> GSK.LSE) and CODEl_EQ / CODEm_EQ (ETF currency
    lines, e.g. RBTXl_EQ -> RBTX.LSE)."""
    base = t212_ticker.split('_')[0]
    m = re.match(r'^([A-Z0-9]+)[a-z]?$', base)
    code = m.group(1) if m else base
    return f"{code}.LSE"

def fetch_eodhd_usage():
    """EODHD plan + daily limit from the /api/user endpoint, or None on failure.
    Used to warn before a portfolio add would outgrow the daily call quota. The
    'dailyRateLimit' it reports is the real recurring ceiling for the key (free
    keys often start with a temporary larger buffer, which we deliberately ignore
    — we care about the steady-state limit the user will eventually hit)."""
    url = f"https://eodhd.com/api/user?api_token={EODHD_API_KEY}&fmt=json"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        return {
            "plan": data.get("subscriptionType", "unknown"),
            "limit": data.get("dailyRateLimit", 0),
            "used": data.get("apiRequests", 0),
        }
    except Exception:
        return None

def t212_auth_header():
    """Basic-auth header for Trading 212 from the configured key/secret."""
    creds = f"{get_secret('T212_KEY_ID')}:{get_secret('T212_SECRET')}"
    token = base64.b64encode(creds.encode()).decode()
    return {"Authorization": f"Basic {token}"}

def fetch_t212_instruments():
    """Full T212 instrument metadata (name, ISIN, currencyCode per ticker) in one
    bulk call. Returns [] on error."""
    try:
        resp = requests.get(f"{T212_BASE}/equity/metadata/instruments",
                            headers=t212_auth_header(), timeout=30)
        if resp.status_code != 200:
            print(f"T212 API error: HTTP {resp.status_code}")
            return []
        return resp.json()
    except Exception as e:
        print(f"T212 error: {e}")
        return []

def analyse_news(name, news_items):
    if news_items is None:
        return {"verdict": "ERROR", "reason": None, "guilty_indices": []}
    if len(news_items) == 0:
        return {"verdict": "NO_NEWS", "reason": None, "guilty_indices": []}
    if not LLM_API_KEY or not LLM_BASE_URL:
        print(f"⚠️ CONFIG ERROR: Missing LLM_API_KEY or LLM_BASE_URL for {name}.")
        return {"verdict": "ERROR", "reason": None, "guilty_indices": []}

    numbered_news = "\n".join(
        f"[{i+1}] [{item['date']}] {item['title']}" + (f"\n  {item['summary'][:200]}" if item['summary'] else "")
        for i, item in enumerate(news_items)
    )

    prompt = (
        f"You are a strict quantitative risk manager for a capital-preservation-first ISA portfolio. "
        f"Review these recent news items for {name} (a UK-listed equity). "
        f"Reply 'FAIL' only if the news indicates severe fundamental risks such as "
        f"fraud, criminal investigations, bankruptcy, insolvency, major credit downgrades, or regulatory sanctions. "
        f"Sector-wide macroeconomic concerns, routine earnings misses, or analyst target price changes do NOT warrant FAIL. "
        f"Reply 'PASS' for all other cases.\n\n"
        f"If FAIL, also provide on separate lines:\n"
        f"REASON: one sentence explaining the specific risk\n"
        f"ARTICLES: comma-separated numbers of the articles that triggered FAIL (e.g. 2,5)\n\n"
        f"News items:\n{numbered_news}"
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
        content = resp.json()['choices'][0]['message']['content'].strip()
        lines = content.split('\n')
        verdict = "FAIL" if "FAIL" in lines[0].upper() else "PASS"
        reason = None
        guilty_indices = []
        if verdict == "FAIL":
            for line in lines[1:]:
                line = line.strip()
                if line.upper().startswith("REASON:"):
                    reason = line[7:].strip()
                elif line.upper().startswith("ARTICLES:"):
                    try:
                        nums = line[9:].strip().split(',')
                        guilty_indices = [int(n.strip()) - 1 for n in nums if n.strip().isdigit()]
                    except Exception:
                        pass
        return {"verdict": verdict, "reason": reason, "guilty_indices": guilty_indices}
    except Exception as e:
        print(f"❌ LLM API Error for {name}: {e}")
        return {"verdict": "ERROR", "reason": None, "guilty_indices": []}

def evaluate_gates(closes, news_items, name):
    sma_pass = closes[-1] > statistics.mean(closes)
    vol_pass = abs((closes[-1] - closes[-2]) / closes[-2]) * 100 < 5.0
    news_result = analyse_news(name, news_items)
    verdict = news_result["verdict"]

    if verdict == "NO_NEWS":
        news_pass, news_icon = True, "🤷‍♂️"
    elif verdict == "FAIL":
        news_pass, news_icon = False, "👎"
    elif verdict == "ERROR":
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
        "news_reason": news_result["reason"],
        "news_guilty": news_result["guilty_indices"],
    }
