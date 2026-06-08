# Copyright (c) 2026 Clement Ha
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# Usage: python3 /app/check_quota.py
#
# Projects whether adding ONE more holding would outgrow the EODHD daily call
# quota, so the agent can warn the user (and suggest a paid plan) before the add.
# Reasons about the steady-state recurring limit, not today's usage — the free
# tier's temporary launch buffer masks the problem early but doesn't change the
# eventual ceiling.
import json
from lib import fetch_eodhd_usage

CONFIG_PATH = '/app/portfolio_targets.json'

# Each report run spends 1 EOD call + 1 news call per holding, and the scheduler
# fires two runs/day (morning + evening) by default → ~4 calls/holding/day.
CALLS_PER_TICKER_PER_DAY = 4

def main():
    try:
        with open(CONFIG_PATH) as f:
            holdings = json.load(f).get("holdings", {})
        current = len(holdings)
    except Exception:
        current = 0

    projected = current + 1  # the pending add
    usage = fetch_eodhd_usage()

    # Fail open: if we can't read the plan, never block the add.
    if not usage or not usage.get("limit"):
        print("QUOTA_UNKNOWN: Could not read EODHD plan. Proceed without a quota warning.")
        return

    plan = usage["plan"]
    limit = usage["limit"]
    needed = projected * CALLS_PER_TICKER_PER_DAY

    if needed > limit:
        max_tickers = limit // CALLS_PER_TICKER_PER_DAY
        print(f"QUOTA_WARN: Adding this holding makes {projected} stocks, needing ~{needed} "
              f"EODHD calls/day — over your '{plan}' plan limit of {limit}/day "
              f"(comfortably covers ~{max_tickers} stocks).")
        print("  Relay to the user: once over the limit, some report lines may show incomplete "
              "data. Suggest upgrading to a paid EODHD plan if they want more holdings.")
    else:
        print(f"QUOTA_OK: {projected} stocks need ~{needed} EODHD calls/day, "
              f"within the '{plan}' plan limit of {limit}/day.")

if __name__ == "__main__":
    main()
