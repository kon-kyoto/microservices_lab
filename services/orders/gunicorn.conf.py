import os
import multiprocessing
from dotenv import load_dotenv

load_dotenv()


def get_workers():
    env = os.getenv("FLASK_ENV", "dev")

    if env == "prod":
        return 3
    else:
        return 1


workers = get_workers()
threads = 2
worker_class = "gthread"
bind = "0.0.0.0:5003"

timeout = 30
graceful_timeout = 30  # limit timeout with shutdown
keepalive = 5

max_requests = 1000
max_requests_jitter = 50
preload_app = True

access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)sms'
)

limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
