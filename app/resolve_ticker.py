# Copyright (c) 2026 Clement Ha
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# Usage: python3 /app/resolve_ticker.py "GSK"
import sys
from lib import search_eodhd, fetch_eod_data, eodhd_ticker_from_t212, fetch_t212_instruments

# London-traded lines settle in pence (GBX) or occasionally GBP. A fund can list
# multiple currency classes under ONE ISIN (e.g. RBTX=GBX, RBOT=USD), so ISIN
# alone cannot pick the UK line — currency is the real discriminator.
UK_CURRENCIES = ("GBX", "GBP")

def pick_eodhd_uk_line(results):
    """From EODHD search results, pick the LSE GBP/GBX line for the most relevant
    fund. Anchors on the top LSE result's ISIN, then selects the GBX/GBP currency
    line of that same fund. Returns (row, warning)."""
    lse = [r for r in results if r.get('Exchange') == 'LSE']
    if not lse:
        if results:
            return results[0], f"no LSE listing found (using {results[0].get('Exchange')} line)"
        return None, "no EODHD results"

    anchor_isin = lse[0].get('ISIN')
    same_fund = [r for r in lse if r.get('ISIN') == anchor_isin] or lse
    for cur in UK_CURRENCIES:
        for r in same_fund:
            if (r.get('Currency') or '').upper() == cur:
                return r, None
    return same_fund[0], f"no GBP/GBX line on LSE; using {same_fund[0].get('Currency')} line"

def find_t212_uk_line(instruments, isin):
    """Find the T212 instrument matching the ISIN AND a UK trading currency.
    Returns (ticker, currency, warning)."""
    matches = [i for i in instruments if isin and i.get('isin') == isin]
    for cur in UK_CURRENCIES:
        for i in matches:
            if (i.get('currencyCode') or '').upper() == cur:
                return i.get('ticker'), cur, None
    if matches:
        m = matches[0]
        return m.get('ticker'), (m.get('currencyCode') or '?').upper(), \
            f"no GBP/GBX T212 line; using {m.get('currencyCode')} line"
    return None, None, "no T212 instrument with matching ISIN"

def validate_eodhd(ticker):
    """Confirm the EODHD ticker actually returns price data (catches bad/guessed
    tickers like IGLDd.EQ before they get saved into the portfolio)."""
    return bool(fetch_eod_data(ticker))

def search_t212_by_name(instruments, query):
    """Fallback: search T212 instrument list directly by name when EODHD is
    unavailable. Prefers UK-currency (GBX/GBP) instruments since ISA accounts
    trade the London lines."""
    query_lower = query.lower()
    query_words = query_lower.split()
    uk = [i for i in instruments if (i.get('currencyCode') or '').upper() in UK_CURRENCIES]

    def first_match(pool, predicate):
        for inst in pool:
            if predicate(inst):
                return inst
        return None

    # 1. Exact name match — UK lines first, then all
    m = first_match(uk, lambda i: i.get('name', '').lower() == query_lower)
    if m: return m
    m = first_match(instruments, lambda i: i.get('name', '').lower() == query_lower)
    if m: return m

    # 2. Ticker code match (e.g. user typed "GSK") — UK lines first
    m = first_match(uk, lambda i: i.get('ticker', '').split('_')[0].lower() == query_lower)
    if m: return m
    m = first_match(instruments, lambda i: i.get('ticker', '').split('_')[0].lower() == query_lower)
    if m: return m

    # 3. All query words present in instrument name — UK lines first
    m = first_match(uk, lambda i: all(w in i.get('name', '').lower() for w in query_words))
    if m: return m
    m = first_match(instruments, lambda i: all(w in i.get('name', '').lower() for w in query_words))
    if m: return m

    # 4. Any long query word starts the instrument name — UK lines first
    m = first_match(uk, lambda i: any(i.get('name', '').lower().startswith(w) for w in query_words if len(w) > 2))
    if m: return m
    m = first_match(instruments, lambda i: any(i.get('name', '').lower().startswith(w) for w in query_words if len(w) > 2))
    if m: return m

    return None

def main():
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    if not query:
        print("Usage: python3 /app/resolve_ticker.py <stock name>")
        sys.exit(1)

    # --- Primary path: EODHD search -> ISIN + currency match on both sides ---
    results = search_eodhd(query)
    if results:
        row, eodhd_warn = pick_eodhd_uk_line(results)
        if row:
            name = row.get('Name', query)
            isin = row.get('ISIN', '')
            eodhd_ticker = f"{row.get('Code')}.{row.get('Exchange')}"
            eodhd_cur = (row.get('Currency') or '?').upper()

            instruments = fetch_t212_instruments()
            if not instruments:
                print(f"RETRY: T212 instrument list unavailable (API error or rate limit).")
                print(f"  EODHD ticker: {eodhd_ticker} ({eodhd_cur})")
                print(f"  Tell the user: Trading 212 is temporarily unavailable. Please try again in a minute.")
                return
            t212_ticker, t212_cur, t212_warn = find_t212_uk_line(instruments, isin)

            if not t212_ticker:
                print(f"NOT FOUND: {name} — no T212 instrument matched ISIN {isin}.")
                print(f"  EODHD ticker: {eodhd_ticker} ({eodhd_cur})")
                print(f"  Tell the user: cannot proceed without a confirmed T212 ticker. Ask them to provide it manually.")
            elif not validate_eodhd(eodhd_ticker):
                print(f"NOT FOUND: {name} — EODHD ticker {eodhd_ticker} returned no price data.")
                print(f"  Tell the user: cannot proceed without valid market data. Ask them to provide the EODHD ticker manually.")
            else:
                print(f"RESOLVED: {name}")
                print(f"  T212 ticker:  {t212_ticker}")
                print(f"  EODHD ticker: {eodhd_ticker}")
                print(f"  Currency: {eodhd_cur}")
                print(f"  ISIN: {isin}")
                if eodhd_cur != (t212_cur or '').upper():
                    print(f"  WARNING: currency mismatch — EODHD {eodhd_cur} vs T212 {t212_cur}. Tell the user.")
                if eodhd_cur not in UK_CURRENCIES:
                    print(f"  WARNING: not a GBP/GBX line — prices will be in {eodhd_cur}. Tell the user.")
                if eodhd_warn:
                    print(f"  NOTE: {eodhd_warn}")
                if t212_warn:
                    print(f"  NOTE: {t212_warn}")
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
    t212_cur = (inst.get('currencyCode') or '?').upper()
    eodhd_ticker = eodhd_ticker_from_t212(t212_ticker)

    if not validate_eodhd(eodhd_ticker):
        print(f"NOT FOUND: {name} — derived EODHD ticker {eodhd_ticker} returned no price data.")
        print(f"  Tell the user: cannot proceed without valid market data. Ask them to provide the EODHD ticker manually.")
        sys.exit(1)

    print(f"RESOLVED (via T212): {name}")
    print(f"  T212 ticker:  {t212_ticker}")
    print(f"  EODHD ticker: {eodhd_ticker}")
    print(f"  Currency: {t212_cur}")
    print(f"  ISIN: {isin}")
    if t212_cur not in UK_CURRENCIES:
        print(f"  WARNING: not a GBP/GBX line — prices will be in {t212_cur}. Tell the user.")

if __name__ == "__main__":
    main()
