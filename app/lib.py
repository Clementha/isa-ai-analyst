# Copyright (c) 2026 Clement Ha
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
import os
import re
import json
import html
import base64
import datetime
import statistics
import requests
import urllib.parse

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

# Stock-name / ticker inputs that reach the resolver scripts: allow only the
# characters real names and tickers actually use (letters, digits, space, and
# . & - ( ) / '). Defence-in-depth against malformed API calls and against
# untrusted input being interpolated into a command line.
ALLOWED_QUERY = re.compile(r"^[A-Za-z0-9 .&()/'\-]{1,64}$")

def is_valid_query(q):
    return bool(q) and bool(ALLOWED_QUERY.match(q))

def search_eodhd(query):
    url = f"https://eodhd.com/api/search/{urllib.parse.quote(query, safe='')}"
    try:
        resp = requests.get(url, params={"api_token": EODHD_API_KEY, "fmt": "json"}, timeout=10)
        return resp.json() if resp.status_code == 200 else []
    except Exception:
        return []

def fetch_eod_data(symbol):
    url = f"https://eodhd.com/api/eod/{urllib.parse.quote(symbol, safe='')}"
    try:
        resp = requests.get(url, params={"api_token": EODHD_API_KEY, "fmt": "json", "period": "d"}, timeout=10)
        data = resp.json()
        return data[-20:] if isinstance(data, list) and len(data) > 0 else []
    except Exception:
        return []

NEWS_WINDOW_DAYS = 30

def fetch_news(symbol):
    """Fetch recent news for a symbol.

    Returns (items, newest_date) where:
      items       — articles within the last NEWS_WINDOW_DAYS, or None on API error
      newest_date — display date of the most recent article of ANY age, or None if
                    EODHD has no coverage for this instrument at all.

    We deliberately fetch without a `from` filter and window client-side, so a
    single API call tells us both "is there news now?" and "does this instrument
    have news coverage at all?" — many ETFs and investment trusts have none, and
    that is worth reporting differently from a quiet news month.
    """
    url = "https://eodhd.com/api/news"
    params = {"api_token": EODHD_API_KEY, "s": symbol, "limit": 10, "fmt": "json"}
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            print(f"⚠️ EODHD news error for {symbol}: HTTP {resp.status_code} — {resp.text[:100]}")
            return None, None  # API error — distinct from genuine no-news
        news = resp.json()
        if not isinstance(news, list):
            print(f"⚠️ EODHD news unexpected response for {symbol}: {str(news)[:100]}")
            return None, None
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=NEWS_WINDOW_DAYS)
        items, newest_dt, newest_date = [], None, None
        for article in news:
            raw_date = article.get('date', '')
            try:
                published = datetime.datetime.fromisoformat(raw_date.replace('Z', '+00:00'))
                date_str = published.strftime('%d %b')
            except Exception:
                published, date_str = None, (raw_date[:10] if raw_date else '?')
            if published and (newest_dt is None or published > newest_dt):
                newest_dt, newest_date = published, published.strftime('%d %b %Y')
            # Undated articles are kept — we cannot prove they are stale.
            if published and published < cutoff:
                continue
            items.append({
                "date": date_str,
                "title": html.unescape(article.get('title', '')),
                "summary": html.unescape(article.get('content', '') or '')
            })
        return items, newest_date  # [] means no news in window, None means error
    except Exception as e:
        print(f"⚠️ EODHD news exception for {symbol}: {e}")
        return None, None

def eodhd_ticker_from_t212(t212_ticker):
    """Derive an EODHD LSE ticker from a T212 ticker. Handles both CODE_LSE_EQ
    (equities, e.g. GSK_LSE_EQ -> GSK.LSE) and CODEl_EQ / CODEm_EQ (ETF currency
    lines, e.g. RBTXl_EQ -> RBTX.LSE)."""
    base = t212_ticker.split('_')[0]
    m = re.match(r'^([A-Z0-9]+)[a-z]?$', base)
    code = m.group(1) if m else base
    return f"{code}.LSE"

def fetch_eodhd_usage():
    """EODHD plan + quota from the /api/user endpoint, or None on failure. Used to
    warn before a portfolio add would outgrow available EODHD calls. Returns both
    'dailyRateLimit' and 'extraLimit': extraLimit is a pool of purchased/bonus
    calls on top of the daily allowance (e.g. a paid call package), so the real
    headroom is limit + extra — callers must count both, not just the daily."""
    url = f"https://eodhd.com/api/user?api_token={EODHD_API_KEY}&fmt=json"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        return {
            "plan": data.get("subscriptionType", "unknown"),
            "limit": data.get("dailyRateLimit", 0),
            "extra": data.get("extraLimit", 0),
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
    bulk call. Returns (instruments, error): error is None on success, "auth" on
    401/403 (bad key, or a key for the wrong T212_MODE — live and practice are
    separate accounts with separate keys/secrets), "unavailable" on any other
    failure. instruments is [] whenever error is set."""
    try:
        resp = requests.get(f"{T212_BASE}/equity/metadata/instruments",
                            headers=t212_auth_header(), timeout=30)
        if resp.status_code in (401, 403):
            return [], "auth"
        if resp.status_code != 200:
            print(f"T212 API error: HTTP {resp.status_code}")
            return [], "unavailable"
        return resp.json(), None
    except Exception as e:
        print(f"T212 error: {e}")
        return [], "unavailable"

INSTRUMENT_CACHE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), f"instruments_cache.{T212_MODE}.json")
INSTRUMENT_CACHE_TTL_DAYS = 30

def get_instrument_currencies(required_tickers=()):
    """Map of T212 ticker -> currencyCode, cached on disk.

    T212 quotes each line in its own currency (GBX for most LSE equities, but GBP
    for some ETFs and EUR/USD for foreign-denominated ones), and the ticker suffix
    does NOT tell you which. Only this metadata does, so holding values must never
    assume a unit.

    The metadata call returns ~17k instruments, so it is cached and refetched only
    when the cache is older than INSTRUMENT_CACHE_TTL_DAYS or is missing a ticker
    you currently hold (i.e. you bought something new). Returns {} if unavailable.
    """
    required = {t for t in (required_tickers or ()) if t}
    cached = None
    try:
        with open(INSTRUMENT_CACHE_PATH) as f:
            cached = json.load(f)
        fetched_at = datetime.datetime.fromisoformat(cached["fetched_at"])
        age_days = (datetime.datetime.now(datetime.timezone.utc) - fetched_at).days
        currencies = cached["currencies"]
        if age_days < INSTRUMENT_CACHE_TTL_DAYS and required.issubset(currencies.keys()):
            return currencies
    except Exception:
        pass  # missing/corrupt cache — refetch below

    instruments, error = fetch_t212_instruments()
    if error:
        print(f"⚠️ T212 instrument metadata unavailable ({error}) — cannot confirm currencies.")
        # A stale cache still beats guessing a unit.
        return (cached or {}).get("currencies", {})

    currencies = {i["ticker"]: (i.get("currencyCode") or "")
                  for i in instruments if i.get("ticker")}
    try:
        with open(INSTRUMENT_CACHE_PATH, "w") as f:
            json.dump({"fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                       "currencies": currencies}, f)
    except Exception as e:
        print(f"⚠️ Could not write instrument cache: {e}")
    return currencies

_FX_CACHE = {}

def fetch_fx_to_gbp(currency):
    """Multiplier converting `currency` into GBP, or None if it can't be determined.

    GBX is pence, so 0.01. Anything else non-GBP needs a real rate, fetched from
    EODHD's FOREX feed. Memoised for the life of the process, so a currency is
    only ever fetched once per run no matter how many holdings use it."""
    if currency == "GBP":
        return 1.0
    if currency == "GBX":
        return 0.01
    if currency in _FX_CACHE:
        return _FX_CACHE[currency]
    data = fetch_eod_data(f"{currency}GBP.FOREX")
    rate = None
    if not data:
        print(f"⚠️ No FX rate available for {currency}→GBP.")
    else:
        try:
            rate = float(data[-1]['close'])
        except Exception:
            print(f"⚠️ Unreadable FX rate for {currency}→GBP.")
    _FX_CACHE[currency] = rate
    return rate

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
