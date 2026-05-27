import requests
import datetime

BANK_HOLIDAYS_URL = "https://www.gov.uk/bank-holidays/england-and-wales.json"

KNOWN_HOLIDAY     = "2026-05-25"  # Spring Bank Holiday (Monday)
KNOWN_TRADING_DAY = "2026-05-27"  # Tuesday — normal trading day
KNOWN_SATURDAY    = "2026-05-23"  # Saturday
KNOWN_SUNDAY      = "2026-05-24"  # Sunday
KNOWN_MONDAY      = "2026-05-18"  # Monday — normal trading day

def fetch_bank_holidays():
    response = requests.get(BANK_HOLIDAYS_URL, timeout=10)
    response.raise_for_status()
    events = response.json().get("events", [])
    return {e["date"] for e in events}

def is_weekend(date_str):
    return datetime.date.fromisoformat(date_str).weekday() >= 5

passed = 0
failed = 0

def check(label, condition):
    global passed, failed
    if condition:
        print(f"  ✅ PASS — {label}")
        passed += 1
    else:
        print(f"  ❌ FAIL — {label}")
        failed += 1

print("\n🧪 Bank Holiday & Weekend Tests\n")

# --- Bank holiday checks ---
print("Bank Holidays (gov.uk API):")
try:
    holidays = fetch_bank_holidays()
    check("gov.uk API is reachable and returned data", len(holidays) > 0)
    check(f"{KNOWN_HOLIDAY} (Spring Bank Holiday) is in the list", KNOWN_HOLIDAY in holidays)
    check(f"{KNOWN_TRADING_DAY} (normal trading day) is NOT in the list", KNOWN_TRADING_DAY not in holidays)
except Exception as e:
    print(f"  ❌ FAIL — Could not fetch bank holidays: {e}")
    failed += 1

# --- Weekend checks ---
print("\nWeekend detection:")
check(f"{KNOWN_SATURDAY} is detected as weekend", is_weekend(KNOWN_SATURDAY))
check(f"{KNOWN_SUNDAY} is detected as weekend", is_weekend(KNOWN_SUNDAY))
check(f"{KNOWN_MONDAY} is NOT detected as weekend", not is_weekend(KNOWN_MONDAY))
check(f"{KNOWN_TRADING_DAY} is NOT detected as weekend", not is_weekend(KNOWN_TRADING_DAY))

print(f"\nResult: {passed} passed, {failed} failed")
if failed == 0:
    print("✅ All checks passed. Safe to merge.\n")
else:
    print("❌ Some checks failed. Do not merge.\n")
