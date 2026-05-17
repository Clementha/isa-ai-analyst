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

def find_t212_ticker(isin, name, code, exchange):
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
            return None
        instruments = resp.json()

        # 1. ISIN match — most reliable
        if isin:
            for inst in instruments:
                if inst.get('isin') == isin:
                    return inst.get('ticker')

        # 2. Constructed ticker pattern (e.g. GSK_LSE_EQ) — common T212 format
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
    except Exception as e:
        print(f"T212 error: {e}")
        return None

def main():
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    if not query:
        print("Usage: python3 /app/resolve_ticker.py <stock name>")
        sys.exit(1)

    results = search_eodhd(query)
    if not results:
        print(f"No EODHD results found for '{query}'.")
        sys.exit(1)

    lse = [r for r in results if r.get('Exchange') == 'LSE']
    best = lse[0] if lse else results[0]

    name = best.get('Name', query)
    isin = best.get('ISIN', '')
    code = best.get('Code', '')
    exchange = best.get('Exchange', '')
    eodhd_ticker = f"{code}.{exchange}"

    t212_ticker = find_t212_ticker(isin, name, code, exchange)

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

if __name__ == "__main__":
    main()
