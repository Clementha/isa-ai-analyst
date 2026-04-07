import time
import subprocess
import schedule
import os
import re
import datetime

ENGINE_PATH = '/app/math_engine.py'
HEARTBEAT_PATH = '/root/.openclaw/workspace/HEARTBEAT.md'
current_times = []

def run_math_engine():
    # 🛑 WEEKEND CHECK
    if datetime.datetime.now().weekday() >= 5:
        print("🛑 Weekend detected. LSE Market is closed. Skipping execution.")
        return

    print("⏰ Target time reached! Triggering Quantitative Engine...")
    subprocess.run(["python3", ENGINE_PATH])

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

    # Fallback to UK market hours if file is empty/broken
    if not new_times:
        new_times = ["08:30", "16:00"]

    if set(new_times) != set(current_times):
        print(f"🔄 Schedule update detected! New run times: {new_times}")
        schedule.clear()
        for t in new_times:
            schedule.every().day.at(t).do(run_math_engine)
        current_times = new_times

reload_schedule()

while True:
    reload_schedule()
    schedule.run_pending()
    time.sleep(60)