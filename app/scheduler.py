# Copyright (c) 2026 Clement Ha
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
import time
import subprocess
import schedule
import os
import re
import datetime
import fcntl
import sys

# --- SINGLE INSTANCE LOCK ---
LOCK_FILE = '/tmp/isa_scheduler.lock'
lock_fp = open(LOCK_FILE, 'w')
try:
    # Try to grab an exclusive, non-blocking lock
    fcntl.lockf(lock_fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
    print("⚠️ Duplicate scheduler detected by hot-reload. Shutting down this instance.")
    sys.exit(0)
# ----------------------------

ENGINE_PATH = '/app/math_engine.py'
HEARTBEAT_PATH = '/root/.openclaw/workspace/HEARTBEAT.md'
current_times = []

def run_math_engine(session):
    # 🛑 WEEKEND CHECK
    if datetime.datetime.now().weekday() >= 5:
        print("🛑 Weekend detected. LSE Market is closed. Skipping execution.")
        return

    label = "Morning Briefing" if session == "morning" else "Evening Analysis"
    print(f"⏰ Target time reached! Triggering {label}...")
    subprocess.run(["python3", ENGINE_PATH, session])

def reload_schedule():
    global current_times
    new_times = []

    if os.path.exists(HEARTBEAT_PATH):
        try:
            with open(HEARTBEAT_PATH, 'r') as f:
                content = f.read()
                extracted = re.findall(r'\b(?:[01]\d|2[0-3]):[0-5]\d\b', content)
                new_times = list(set(extracted))
        except Exception:
            pass

    # Fallback: morning briefing + post-market evening analysis
    if not new_times:
        new_times = ["08:30", "17:30"]

    if set(new_times) != set(current_times):
        print(f"🔄 Schedule update detected! New run times: {new_times}")
        schedule.clear()
        for t in new_times:
            session = "evening" if int(t.split(':')[0]) >= 14 else "morning"
            schedule.every().day.at(t).do(run_math_engine, session)
        current_times = new_times

reload_schedule()

while True:
    reload_schedule()
    schedule.run_pending()
    time.sleep(60)