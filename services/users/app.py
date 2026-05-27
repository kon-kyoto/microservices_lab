import os
from dotenv import load_dotenv

from flask import Flask, request, jsonify

import jwt
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

app = Flask(__name__)
load_dotenv()

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

@app.route('/user/<find_id>', methods=['GET'])
def get_user(find_id):
    token = request.headers.get("Authorization").replace("Bearer ", "")

    try:
        jwt_data = jwt.decode(
                token,
                os.getenv('SECRET_KEY'), 
                os.getenv('JWT_ALGORITHM')
            )

        if jwt_data['user_id'] != int(find_id):
            return jsonify({'message':'permission denied'})

        
        with get_db_cursor() as cur:
            cur.execute(
                    "SELECT * FROM users WHERE id = %s",
                    (find_id,)
                )
            data_row = cur.fetchone()
            if not data_row:
                return jsonify({'message': 'user not found'}), 404

        return jsonify({'username': data_row['username'], 'email': data_row['email']}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'token is dead'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'token is invalid'}), 401
    except Exception as e:
        app.logger.error(f"[ERROR] {str(e)}")
        return jsonify({'message':'server error'}), 500

@app.route('/user_change', methods=['PUT'])
def user_change():
    token = request.headers.get('Authorization').replace('Bearer ', '')
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')

    try:
        jwt_data = jwt.decode(
                token,
                os.getenv('SECRET_KEY'),
                os.getenv('JWT_ALGORITHM')
            )
        user_id = jwt_data['user_id']

        with get_db_cursor() as cur:
            if email:
                cur.execute(
                        "UPDATE users SET username = %s WHERE id = %s",
                        (username, user_id)
                    )
            if username:
                cur.execute(
                        "UPDATE users SET username = %s WHERE id = %s",
                        (username, user_id)
                    )
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'token is dead'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'token is invalid'}), 401
    except Exception as e:
        app.logger.error(f"[ERROR] {str(e)}")
        return jsonify({'message':'server error'}), 500


    return jsonify({'message': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5001')
