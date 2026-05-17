import time
import sys

print("Time generator started. Press Ctrl+C to stop it")
while True:
    try:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}]")
        sys.stdout.flush()
        time.sleep(2)
    except KeyboardInterrupt:
        break
