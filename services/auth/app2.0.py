import os
from dotenv import load_dotenv

from flask import Flask, request, jsonify
import bcrypt

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

load_dotenv()
app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
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

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        with get_db_cursor() as cur:
            cur.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                    (username, email, password_hash.decode('utf-8'))
                )

            user_id = cur.fetchone()['id']

            return jsonify({'message': 'user created', 'user_id': user_id}), 201
    except psycopg2.IntegrityError:
        return jsonify({"error": "username or email is already exist"}), 400

if __name__ == "__main__":
    app.run(host = "0.0.0.0",  port = 5000)
