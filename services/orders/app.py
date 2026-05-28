import os
from dotenv import load_dotenv

from flask import Flask, request, jsonify
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

app = Flask(__name__)
load_dotenv()

def get_db_connection():
    return psycopg2.connect(
            host=os.getenv('POSTGRES_HOST')
            database=os.getenv('DB_NAME')
            user=os.getenv('POSTGRES_USER')
            password=os.getenv('POSTGRES_PASSWORD')
            cursor_factory=RealDictCursor
        )

def get_db_cursor():
    conn = get_db_connection()
    try:
        yield conn.cursor()
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        conn.close()

