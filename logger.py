import time
import os

LOG_FILE = "/data/log.txt"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

while True:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"New log in {LOG_FILE}")
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}]\n")
        time.sleep(3)
    except KeyboardInterrupt:
        break
