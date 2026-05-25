import os
from dotenv import load_dotenv()

import psycopq2
from psycopq2.extras import RealDictCursor
from contextlib import contextmanager

load_dotenv()

def get_db_connection():
    return psycopq2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('AUTH_DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            cursor_factory=RealDictCursor
        )

@contextmanager
def get_db_cursor():
    conn = get_db_connection()
    try:
        yield conn.cursor()
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
