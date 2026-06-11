# Copyright (c) 2026 Clement Ha
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# Usage: python3 /app/check_stock.py "BAE Systems"
#    or: python3 /app/check_stock.py "BA.LSE"
import sys
import datetime
from lib import search_eodhd, fetch_eod_data, fetch_news, evaluate_gates, is_valid_query

def main():
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    if not query:
        print("Usage: python3 /app/check_stock.py <stock name or EODHD ticker>")
        sys.exit(1)
    if not is_valid_query(query):
        print(f"INVALID: '{query}' contains unexpected characters. Use only letters, numbers, "
              "spaces and . & - ( ) / '. Ask the user to re-enter the stock name.")
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
        name = match.get('Name', query)
        eodhd_ticker = f"{match.get('Code', '')}.{match.get('Exchange', '')}"

    data = fetch_eod_data(eodhd_ticker)
    if not data or len(data) < 2:
        print(f"ERROR: Insufficient price data for {eodhd_ticker}. Check the ticker or EODHD daily quota.")
        sys.exit(1)

    closes = [float(day['close']) for day in data]
    latest = closes[-1]
    raw_date = data[-1].get('date', '')
    try:
        price_date = datetime.datetime.strptime(raw_date, '%Y-%m-%d').strftime('%a %d %b')
    except Exception:
        price_date = raw_date

    gates = evaluate_gates(closes, fetch_news(eodhd_ticker), name)

    print(f"{name} ({eodhd_ticker}): £{latest:.4f} (as of {price_date})")
    print(f"SMA {gates['sma_icon']} | Vol {gates['vol_icon']} | News {gates['news_icon']}")
    print(f"Overall: {'🟢 GREEN — would qualify for a BUY signal' if gates['all_green'] else '🔴 RED — would not qualify'}")

if __name__ == "__main__":
    main()
