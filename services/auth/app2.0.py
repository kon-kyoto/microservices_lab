import os
from dotenv import load_dotenv()

import bcrypt

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

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = daya.get('email')

    password_hash = bcrypt.hashow(password.encode('utf-8'), bcrypt.gensalt())r

    try:
        with get_db_cursor() as cur:
            cur.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (%s %s %s) RETURING id",
                    (username, email, password_hash.decode('utf-8'))
                )

            user_id = cur.fetchone()['id']

            return jsonify({'message': 'user created', 'user_id': user_id}), 201
    except psycopq2.InegrityError:
        return jsonify({"error": "username or email is already exist"}), 400
