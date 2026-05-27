import os
from dotenv import load_dotenv
from functools import wraps

from flask import Flask, request, jsonify, g
import requests

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
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'message': 'missing authorization header'}), 401
        token = auth_header.replace('Bearer ', '')

        try:
            response = requests.post(
                    'http://auth_service:5001/verify',
                    headers={'Authorization': f'Bearer {token}'}
                )
            
            if response.status_code != 200:
                return jsonify({'message': 'invalid token'}), 401

            user_data = response.json()
            g.user_id = user_data.get('user_id')

            return func(*args, **kwargs)

        except requests.exceptions.ConnectionError:
            app.logger.error("Cannot connect to auth_service")
            return jsonify({'message': 'authentication service unavailable'}), 503
        except requests.exceptions.Timeout:
            app.logger.error("Auth service timeout")
            return jsonify({'message': 'authentication service timeout'}), 504
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Auth service request error: {str(e)}")
            return jsonify({'message': 'authentication failed'}), 401
        except Exception as e:
            app.logger.error(f"Unexpected error in token_reader: {str(e)}")
            return jsonify({'message': 'internal server error'}), 500

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

    if str(user_id) != str(find_id):
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
    if not data:
        return jsonify({'message': 'lost data'})

    username = data.get('username')
    email = data.get('email')
    user_id = g.get('user_id')

    if str(user_id) != str(find_id):
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
    
    if str(user_id) != str(find_id):
        return jsonify({'message': 'permission denied'})

    with get_db_cursor() as cur:
        cur.execute(
                "DELETE FROM auth_users WHERE user_id = %s",
                (find_id,)
            )
        cur.execute(
                "DELETE FROM users WHERE id = %s",
                (find_id,)
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
    app.run(host='0.0.0.0', port=5002)
