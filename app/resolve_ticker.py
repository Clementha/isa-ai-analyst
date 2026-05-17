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

def find_t212_ticker(isin, name):
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
        # Match by ISIN first (most reliable)
        if isin:
            for inst in instruments:
                if inst.get('isin') == isin:
                    return inst.get('ticker')
        # Fall back to name substring match
        name_lower = name.lower()
        for inst in instruments:
            if name_lower in inst.get('name', '').lower():
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
    eodhd_ticker = f"{best.get('Code', '')}.{best.get('Exchange', '')}"

    t212_ticker = find_t212_ticker(isin, name)

    if t212_ticker:
        print(f"RESOLVED: {name}")
        print(f"  T212 ticker:  {t212_ticker}")
        print(f"  EODHD ticker: {eodhd_ticker}")
        print(f"  ISIN: {isin}")
    else:
        print(f"PARTIAL: {name} — T212 ticker not found, manual lookup needed.")
        print(f"  EODHD ticker: {eodhd_ticker}")
        print(f"  ISIN: {isin}")

if __name__ == "__main__":
    main()
