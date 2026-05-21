# Copyright (c) 2026 Clement Ha
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# Usage: python3 /app/resolve_ticker.py "GSK"
import sys
import base64
import requests
from lib import get_secret, search_eodhd

T212_KEY_ID = get_secret("T212_KEY_ID")
T212_SECRET = get_secret("T212_SECRET")

def fetch_t212_instruments():
    credentials = f"{T212_KEY_ID}:{T212_SECRET}"
    auth = base64.b64encode(credentials.encode()).decode()
    try:
        resp = requests.get(
            "https://live.trading212.com/api/v0/equity/metadata/instruments",
            headers={"Authorization": f"Basic {auth}"},
            timeout=30
        )
        if resp.status_code != 200:
            print(f"T212 API error: HTTP {resp.status_code}")
            return []
        return resp.json()
    except Exception as e:
        print(f"T212 error: {e}")
        return []

def find_t212_ticker(instruments, isin, name, code, exchange):
    # 1. ISIN match — most reliable
    if isin:
        for inst in instruments:
            if inst.get('isin') == isin:
                return inst.get('ticker')

    # 2. Constructed ticker pattern (e.g. GSK_LSE_EQ)
    constructed = f"{code}_{exchange}_EQ"
    for inst in instruments:
        if inst.get('ticker') == constructed:
            return constructed

    # 3. Full name substring match
    name_lower = name.lower()
    for inst in instruments:
        if name_lower in inst.get('name', '').lower():
            return inst.get('ticker')

    # 4. Short code word match against instrument name
    code_lower = code.lower()
    for inst in instruments:
        inst_words = inst.get('name', '').lower().split()
        if code_lower in inst_words:
            return inst.get('ticker')

    return None

def search_t212_by_name(instruments, query):
    """Fallback: search T212 instrument list directly by name when EODHD is unavailable.
    Prefers LSE-listed instruments throughout (ISA accounts hold UK equities)."""
    query_lower = query.lower()
    query_words = query_lower.split()
    lse = [i for i in instruments if '_LSE_' in i.get('ticker', '')]

    def first_match(pool, predicate):
        for inst in pool:
            if predicate(inst):
                return inst
        return None

    # 1. Exact name match — LSE first, then all
    m = first_match(lse, lambda i: i.get('name', '').lower() == query_lower)
    if m: return m
    m = first_match(instruments, lambda i: i.get('name', '').lower() == query_lower)
    if m: return m

    # 2. Ticker code match (e.g. user typed "GSK") — LSE first
    m = first_match(lse, lambda i: i.get('ticker', '').split('_')[0].lower() == query_lower)
    if m: return m
    m = first_match(instruments, lambda i: i.get('ticker', '').split('_')[0].lower() == query_lower)
    if m: return m

    # 3. All query words present in instrument name — LSE first
    m = first_match(lse, lambda i: all(w in i.get('name', '').lower() for w in query_words))
    if m: return m
    m = first_match(instruments, lambda i: all(w in i.get('name', '').lower() for w in query_words))
    if m: return m

    # 4. Any long query word starts the instrument name — LSE first
    m = first_match(lse, lambda i: any(i.get('name', '').lower().startswith(w) for w in query_words if len(w) > 2))
    if m: return m
    m = first_match(instruments, lambda i: any(i.get('name', '').lower().startswith(w) for w in query_words if len(w) > 2))
    if m: return m

    return None

def eodhd_ticker_from_t212(t212_ticker):
    """Derive EODHD ticker from T212 ticker format (e.g. GSK_LSE_EQ -> GSK.LSE)."""
    parts = t212_ticker.split('_')
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return t212_ticker

def main():
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    if not query:
        print("Usage: python3 /app/resolve_ticker.py <stock name>")
        sys.exit(1)

    # --- Primary path: EODHD search + T212 ISIN match ---
    results = search_eodhd(query)
    if results:
        lse = [r for r in results if r.get('Exchange') == 'LSE']
        best = lse[0] if lse else results[0]

        name = best.get('Name', query)
        isin = best.get('ISIN', '')
        code = best.get('Code', '')
        exchange = best.get('Exchange', '')
        eodhd_ticker = f"{code}.{exchange}"

        instruments = fetch_t212_instruments()
        t212_ticker = find_t212_ticker(instruments, isin, name, code, exchange)

        if t212_ticker:
            print(f"RESOLVED: {name}")
            print(f"  T212 ticker:  {t212_ticker}")
            print(f"  EODHD ticker: {eodhd_ticker}")
            print(f"  ISIN: {isin}")
        else:
            print(f"NOT FOUND: {name} — could not match a T212 ticker.")
            print(f"  EODHD ticker: {eodhd_ticker}")
            print(f"  ISIN: {isin}")
            print(f"  Tell the user: cannot proceed without a confirmed T212 ticker. Ask them to provide it manually.")
        return

    # --- Fallback path: search T212 instrument list directly by name ---
    print(f"EODHD search unavailable for '{query}', falling back to T212 name search...")
    instruments = fetch_t212_instruments()
    if not instruments:
        print(f"NOT FOUND: Could not reach T212 API.")
        sys.exit(1)

    inst = search_t212_by_name(instruments, query)
    if not inst:
        print(f"NOT FOUND: No match for '{query}' in T212 instruments.")
        print(f"  Tell the user: cannot proceed without a confirmed T212 ticker. Ask them to provide it manually.")
        sys.exit(1)

    t212_ticker = inst.get('ticker', '')
    name = inst.get('name', query)
    isin = inst.get('isin', '')
    eodhd_ticker = eodhd_ticker_from_t212(t212_ticker)

    print(f"RESOLVED (via T212): {name}")
    print(f"  T212 ticker:  {t212_ticker}")
    print(f"  EODHD ticker: {eodhd_ticker}")
    print(f"  ISIN: {isin}")

if __name__ == "__main__":
    main()
