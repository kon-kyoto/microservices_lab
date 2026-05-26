import os
from dotenv import load_dotenv

from flask import Flask, request, jsonify

import bcrypt
import jwt
from datetime import datetime, timedelta

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
            if username:
                cur.execute(
                        "SELECT id FROM users WHERE username = %s LIMIT 1",
                        (username,)
                    )
            else:
                cur.execute(
                        "SELECT id FROM users WHERE email = %s LIMIT 1",
                        (email,)
                    )
            if not cur.fetchone():
                return jsonify({"message": "user not found"}), 400
            user_id = cur.fetchone()['id']

            cur.execute(
                    "SELECT password_hash FROM auth_users WHERE user_id = %s",
                    (user_id,)
                )
            if not bcrypt.checkpw(password.encode('utf-8'), cur.fetchone()['password_hash'].encode('utf-8')):
                return jsonify({"message": "wrong password"}), 400

        token = jwt.encode(
                {
                    "user_id": user_id,
                    "username": username,
                    "exp": datetime.utcnow() + timedelta(hours=int(os.getenv('TIMEDELTA')))
                },
                os.getenv('SECRET_KEY'),
                algorithm=os.getenv('JWT_ALGORITHM')
            )

        return jsonify({'access_token': token}), 200

    except bcrypt.InvalidHash:
        return jsonify({'message': 'invalid hash format in database'}), 500
    except jwt.InvalidTokenError:
        return jsonify({'message': 'token generation error'}), 500
    except psycopg2.OperationalError as e:
        return jsonify({'message': f'database error: {str(e)}'}), 500
    except Exception as e:
        app.logger.error(f"[ERROR]: {str(e)}")
        return jsonify({'message': 'internal server error'}), 500

if __name__ == "__main__":
    app.run(host = "0.0.0.0",  port = 5000)
