import os
from dotenv import load_dotenv

from flask import Flask, request, jsonify, g
from functools import wraps

import jwt
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

app = Flask(__name__)
load_dotenv()

JWT_CONFIG = {
    'algorithm': 'HS256',
    'secret_key': os.getenv('SECRET_KEY'),
    'expires_hours': int(os.getenv('TIMEDELTA', '24'))
}

def token_reader(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            token = request.headers.get('Authorization').replace('Bearer ','')
            jwt_data = jwt.decode(token, JWT_CONFIG['secret_key'], algorithms=[JWT_CONFIG['algorithm']])

            g.user_id = jwt_data.get('user_id')

            return func(*args, **kwargs)

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'token is dead'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'token is invalid'}), 401
        except Exception as e:
            app.logger.error(f"[ERROR] {str(e)}")
            return jsonify({'message':'server error'}), 500

    return wrapper


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

@app.route('/users/<find_id>', methods=['GET'])
@token_reader
def get_user(find_id):
    user_id = g.get('user_id')

    if user_id != find_id:
        return jsonify({'message':'permission denied'})

    
    with get_db_cursor() as cur:
        cur.execute(
                "SELECT * FROM users WHERE id = %s",
                (find_id,)
            )
        data_row = cur.fetchone()
        if not data_row:
            return jsonify({'message': 'user not found'}), 404

    return jsonify({'username': data_row.get('username'), 'email': data_row.get('email')}), 200

@app.route('/users/<find_id>', methods=['PUT'])
@token_reader
def user_change(find_id):
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    user_id = g.get('user_id')
    find_id = int(find_id)

    if user_id != find_id:
        return jsonify({'message': 'permission denied'})

    with get_db_cursor() as cur:
        if email:
            cur.execute(
                    "UPDATE users SET email = %s WHERE id = %s",
                    (email, user_id)
                )
        if username:
            cur.execute(
                    "UPDATE users SET username = %s WHERE id = %s",
                    (username, user_id)
                )

    return jsonify({'message': f'ur account info has been changed'})

@app.route('/users/<find_id>', methods=['DELETE'])
@token_reader
def user_delete(find_id):
    user_id = g.get('user_id')
    find_id = int(find_id)

    with get_db_cursor() as cur:
        cur.execute(
                "DELETE FROM users WHERE id = %s",
                (user_id,)
            )
        cur.execute(
                "DELETE FROM auth_users WHERE user_id = %s",
                (user_id,)
            )

    return jsonify({'message': 'SUCCESS u delete this account'})

@app.route('/users', methods=['GET'])
@token_reader
def users_list():
    user_id = g.get('user_id')
    username = g.get('username')

    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM users")
        result = cur.fetchall()

    return jsonify(result), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5001')
