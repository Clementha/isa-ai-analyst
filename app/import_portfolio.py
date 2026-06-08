# Copyright (c) 2026 Clement Ha
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# Usage:
#   python3 /app/import_portfolio.py            # dry-run: stage a proposal
#   python3 /app/import_portfolio.py --commit   # apply the staged proposal
#
# Builds portfolio_targets.json from the user's ACTUAL Trading 212 holdings.
# Each holding gets an equal default target (25%, matching the README model),
# capped so the total never exceeds the investable space (1 - cash reserve),
# leaving headroom to add more later without trimming an over-weighted position.
# The dry-run stages to a .proposed.json file; --commit atomically swaps it in.
# The agent only runs --commit after the user confirms with "YES".
import sys
import os
import json
import requests
from lib import (t212_auth_header, fetch_t212_instruments, eodhd_ticker_from_t212,
                 fetch_eodhd_usage, T212_BASE)

CONFIG_PATH = '/app/portfolio_targets.json'
PROPOSED_PATH = '/app/portfolio_targets.proposed.json'
UK_CURRENCIES = ("GBX", "GBP")
CALLS_PER_TICKER_PER_DAY = 4  # 2 runs/day x (EOD + news); matches check_quota.py
DEFAULT_STOCK_WEIGHT = 0.25  # per-holding target cap, matching the README 25% model

def load_config():
    """Existing config (to preserve cash %, ISA target, DCA limit) or defaults."""
    defaults = {"isa_allowance_target": 20000, "target_cash_pct": 0.10,
                "daily_dca_limit": 500, "holdings": {}}
    try:
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
        for k, v in defaults.items():
            cfg.setdefault(k, v)
        return cfg
    except Exception:
        return defaults

def fetch_positions():
    """T212 open positions, or None on API error (distinct from [] = no holdings)."""
    try:
        resp = requests.get(f"{T212_BASE}/equity/portfolio",
                            headers=t212_auth_header(), timeout=30)
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data if isinstance(data, list) else None
    except Exception:
        return None

def build_proposal():
    """Returns (cfg, holdings, proposed, cash_pct) or None after printing a
    NO_HOLDINGS / RETRY status line for the agent."""
    cfg = load_config()
    cash_pct = cfg.get("target_cash_pct", 0.10)

    positions = fetch_positions()
    if positions is None:
        print("RETRY: Trading 212 is temporarily unavailable. Ask the user to try again in a minute.")
        return None
    if not positions:
        print("NO_HOLDINGS: No open positions in the Trading 212 account to import.")
        return None

    instruments = fetch_t212_instruments()
    meta = {i.get('ticker'): i for i in instruments} if instruments else {}

    # Compute each holding's £ value (GBX/pence lines -> /100, like the engine).
    holdings = []
    for pos in positions:
        ticker = pos.get('ticker')
        qty = pos.get('quantity', 0) or 0
        price = pos.get('currentPrice', 0) or 0
        value = qty * price / 100
        info = meta.get(ticker, {})
        holdings.append({
            "t212_ticker": ticker,
            "eodhd_ticker": eodhd_ticker_from_t212(ticker),
            "name": info.get('name', ticker),
            "currency": (info.get('currencyCode') or '?').upper(),
            "value": value,
        })

    total = sum(h["value"] for h in holdings)
    if total <= 0:
        print("NO_HOLDINGS: Trading 212 positions have no resolvable market value to weight.")
        return None

    # Equal default target per holding (25%, the README model), capped so the
    # total never exceeds the investable space (1 - cash reserve). With only a
    # few holdings this leaves deliberate unallocated headroom, so the user can
    # add more later without first trimming an over-weighted position.
    n = len(holdings)
    avail_pct = round((1.0 - cash_pct) * 100)
    cap_pct = round(DEFAULT_STOCK_WEIGHT * 100)
    if n * cap_pct <= avail_pct:
        for h in holdings:
            h["pct"] = cap_pct
    else:
        # Too many holdings to all sit at the cap: split the investable space
        # evenly (largest-remainder), giving spare points to the biggest lines.
        base = avail_pct // n
        for h in holdings:
            h["pct"] = base
        order = sorted(range(n), key=lambda i: holdings[i]["value"], reverse=True)
        for i in range(avail_pct - base * n):
            holdings[order[i]]["pct"] += 1

    proposed = {
        "isa_allowance_target": cfg.get("isa_allowance_target", 20000),
        "target_cash_pct": cash_pct,
        "daily_dca_limit": cfg.get("daily_dca_limit", 500),
        "holdings": {
            h["t212_ticker"]: {
                "eodhd_ticker": h["eodhd_ticker"],
                "name": h["name"],
                "target_weight": round(h["pct"] / 100, 2),
            } for h in holdings if h["pct"] > 0
        },
    }
    return cfg, holdings, proposed, cash_pct

def main():
    if "--commit" in sys.argv:
        commit()
        return

    result = build_proposal()
    if not result:
        return
    cfg, holdings, proposed, cash_pct = result

    with open(PROPOSED_PATH, 'w') as f:
        json.dump(proposed, f, indent=2)

    n = len(proposed["holdings"])
    print(f"IMPORT_PROPOSAL: {n} holdings (cash reserve kept at {cash_pct*100:.0f}%)")
    for h in holdings:
        if h["pct"] > 0:
            print(f"  - {h['name']} ({h['t212_ticker']} / {h['eodhd_ticker']}) "
                  f"[{h['currency']}]  £{h['value']:.2f} -> {h['pct']}%")
    for h in holdings:
        if h["pct"] > 0 and h["currency"] not in UK_CURRENCIES:
            print(f"  WARNING: {h['name']} ({h['t212_ticker']}) is a {h['currency']} line, not GBP/GBX — "
                  f"its derived ticker {h['eodhd_ticker']} and weight may be inaccurate. Verify it.")

    existing = cfg.get("holdings", {})
    if existing:
        print(f"  OVERWRITE: This REPLACES your current {len(existing)} holding(s): {', '.join(existing.keys())}.")

    usage = fetch_eodhd_usage()
    needed = n * CALLS_PER_TICKER_PER_DAY
    if usage and usage.get("limit"):
        if needed > usage["limit"]:
            print(f"  QUOTA_WARN: {n} holdings need ~{needed} EODHD calls/day, over your "
                  f"'{usage['plan']}' limit of {usage['limit']}/day. Some report lines may show "
                  f"incomplete data; suggest a paid EODHD plan.")
        else:
            print(f"  QUOTA_OK: {n} holdings need ~{needed} EODHD calls/day, within the "
                  f"'{usage['plan']}' limit of {usage['limit']}/day.")

    print(f"Staged to {PROPOSED_PATH}. After the user confirms with YES, "
          f"run: python3 /app/import_portfolio.py --commit")

def commit():
    try:
        with open(PROPOSED_PATH) as f:
            proposed = json.load(f)
    except Exception:
        print("COMMIT_FAILED: No valid staged proposal found. Run the import first.")
        return
    if not proposed.get("holdings"):
        print("COMMIT_FAILED: Staged proposal has no holdings. Aborting.")
        return
    try:
        os.replace(PROPOSED_PATH, CONFIG_PATH)  # atomic on the same filesystem
    except Exception as e:
        print(f"COMMIT_FAILED: Could not write config: {e}")
        return
    print(f"COMMITTED: Imported {len(proposed['holdings'])} holdings into portfolio_targets.json.")

if __name__ == "__main__":
    main()
