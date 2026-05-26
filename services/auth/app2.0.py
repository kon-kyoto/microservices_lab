import os
from dotenv import load_dotenv

from flask import Flask, request, jsonify

import bcrypt
import jwt

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

    if not username or not password or not email:
        return jsonify({"message": "please fill in the fields: username, email, password"})

    try:
        with get_db_cursor() as cur:
            cur.execute(
                    "INSERT INTO users (username, email) VALUES (%s, %s) RETURNING id",
                    (username, email)
                )
            user_id = cur.fetchone()['id']
            cur.execute(
                   "INSERT INTO auth_users (user_id, password_hash) VALUES (%s, %s)",
                   (user_id, password_hash.decode('utf-8'))
                )

            return jsonify({'message': 'user created', 'user_id': user_id}), 201
    except psycopg2.IntegrityError:
        return jsonify({"error": "username or email is already exist"}), 400
    except Exception:
        return jsonify({"message": "some trubles"}), 501

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    if not(email or username):
        return jsonyfi({'message': 'i need email or username'})

    try:
        with get_db_cursor() as cur:
            cur.execute(
                    "SELECT password_hash FROM auth_users WHERE user_id = (SELECT id FROM users WHERE username = %s LIMIT 1)",
                    (username,)
                )
            if not bcrypt.checkpw(password.encode('utf-8'), cur.fetchone()['password_hash'].encode('utf-8')):
                return jsonify({"message": "wrong password"}), 400
    except TypeError:
        return jsonify({"message": "user not found"}), 400
    except Exception as e:
        return jsonify({"message": e}), 501

    return jsonify({'message': password}), 200

if __name__ == "__main__":
    app.run(host = "0.0.0.0",  port = 5000)
