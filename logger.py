import time
import os

LOG_FILE = "/data/log.txt"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

with open(LOG_FILE, "a") as f:
    while True:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}]\n")
        print(f"New log in {LOG_FILE}")
        try:
            time.sleep(3)
        except KeyboardInterrupt:
            break
