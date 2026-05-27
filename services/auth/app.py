import os
from dotenv import load_dotenv
import re

from flask import Flask, request, jsonify
import redis

import bcrypt
import jwt
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

load_dotenv()
app = Flask(__name__)
redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=int(os.getenv('REDIS_PORT')),
        decode_responses=True 
    )

JWT_CONFIG = {
    'algorithm': 'HS256',
    'secret_key': os.getenv('SECRET_KEY'),
    'expires_hours': int(os.getenv('TIMEDELTA', '24'))
}

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
    if not data:
        return jsonify({'message': 'lost data'})
    
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    if not username or not password or not email:
        return jsonify({"message": "please fill in the fields: username, email, password"})

    email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

    if not re.match(email_pattern, email):
        return jsonify({'message':'email is not valid'})

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

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
    if not data:
        return jsonify({'message': 'lost data'})

    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    if not email and not username:
        return jsonify({'message': 'i need email or username'}), 400
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
            
            user_row = cur.fetchone()
            if not user_row:
                return jsonify({"message": "user not found"}), 400
            
            user_id = user_row['id']

            cur.execute(
                "SELECT password_hash FROM auth_users WHERE user_id = %s",
                (user_id,)
            )
            password_row = cur.fetchone()
            if not password_row:
                return jsonify({"message": "user has no password set"}), 400
            
            if not bcrypt.checkpw(password.encode('utf-8'), password_row['password_hash'].encode('utf-8')):
                return jsonify({"message": "wrong password"}), 400

        token = jwt.encode(
            {
                "user_id": user_id,
                "exp": datetime.utcnow() + timedelta(hours=JWT_CONFIG['expires_hours'])
            },
            JWT_CONFIG['secret_key'],
            algorithm=JWT_CONFIG['algorithm']
        )

        return jsonify({'access_token': token}), 200

    except jwt.InvalidKeyError as e:
        app.logger.error(f"JWT key error: {str(e)}")
        return jsonify({'message': 'token generation error - invalid key'}), 500
    except jwt.InvalidAlgorithmError as e:
        app.logger.error(f"JWT algorithm error: {str(e)}")
        return jsonify({'message': 'token generation error - invalid algorithm'}), 500
    except psycopg2.OperationalError as e:
        app.logger.error(f"Database error: {str(e)}")
        return jsonify({'message': f'database error: {str(e)}'}), 500
    except Exception as e:
        app.logger.error(f"[ERROR]: {str(e)}")
        return jsonify({'message': 'internal server error'}), 500

@app.route('/logout', methods=['POST'])
def logout():
    auth_head = request.headers.get('Authorization')
    if not auth_head:
        return jsonify({'message': 'unknown user'})
    token = auth.replace('Bearer ', '')

    try:
        jwt_data = decode(token, JWT_CONFIG['secret_key'], algorithms = [JWT_CONFIG['algorithm']])
        exp_timestamp = jwt_data['exp']
        current_time = datetime.utcnow().timestamp()
        tt1 = int(exp_timestamp - current_time)

        if tt1 > 0:
            redis_client.setex(f"blacklist:{token}", tt1, "revoked")

        return jsonify({'message': 'logout complite'})
    except:
        return jsonify({'message': 'invalid token'})


@app.route('/verify', methods=['POST'])
def verify():
    try:
        auth_head = request.headers.get('Authorization').replace('Bearer ','')
        if not auth_head:
            return jsonify({'message': 'lost header'})
        token = auth_head.replace('Bearer ', '')

        jwt_data = jwt.decode(token, JWT_CONFIG['secret_key'], algorithms=[JWT_CONFIG['algorithm']])

        return jsonify({'user_id': jwt_data.get('user_id')})

    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'token is dead'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'token is invalid'}), 401
    except Exception as e:
        app.logger.error(f"[ERROR] {str(e)}")
        return jsonify({'message':'server error'}), 500

if __name__ == "__main__":
    app.run(host = "0.0.0.0",  port = 5001)

