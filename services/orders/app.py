import os
from dotenv import load_dotenv
from functools import wraps

from flask import Flask, request, jsonify, g
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

def check_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_head = request.headers.get('Authorization')
        if not auth_head:
            return jsonify({'message', 'empty auth header'})
        token = auth_head.replace('Bearer ', '')
        
        try:
            response = requests.post(
                    'http://auth_service:5001/verify',
                    headers = {'Authorization': f'Bearer {token}'},
                )
            if response.status_code != 200:
                return ({'message': 'invalid token'}), 401

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
            app.logger.error(f"Unexpected error in check_token: {str(e)}")
            return jsonify({'message': 'internal server error'}), 500
    return wrapper

@app.route('/orders', methods=['POST'])
@check_token
def create_order():
    data = request.get_json()
    if not data:
        return jsonify({'message': 'no json'})
    status = 'pending'
    total_amount = data.get('total_amount')
    
    try:
        if not total_amount or int(total_amount) < 1:
            return jsonify({'message': 'total amount can be int and bigger/equale 1'}), 401
    except TypeError:
        return jsonify({'message': 'total amount type error'}), 401

    try:
        with get_db_cursor() as cur:
            cur.execute(
                    "INSERT INTO orders (user_id, total_amount, status) VALUES (%s, %s, %s) RETURNING id",
                    (g.user_id, total_amount, status)
                )
            order_id = cur.fetchone()['id']

        return jsonify({'message': 'SUCCESS', 'order_id': order_id})
    except psycopg2.IntegrityError:
        return jsonify({"error": "username or email is already exist"}), 400
    except Exception:
        return jsonify({"message": "some trubles"}), 501

@app.route('/orders/<order_id>', methods=['GET'])
@check_token
def get_order(order_id):
    try:
        with get_db_cursor() as cur:
            cur.execute(
                    "SELECT * FROM orders WHERE id = %s",
                    (order_id,)
                )
            data_row = cur.fetchone()
            if not data_row:
                return jsonify({'message': 'order id not found'}), 200

            return jsonify(data_row), 200
    except Exception:
        return jsonify({'message': 'my fail'}), 500

@app.route('/orders/user/<user_id>', methods=['GET'])
@check_token
def get_users_orders(user_id):
    try:
        with get_db_cursor() as cur:
            cur.execute(
                    "SELECT * FROM orders WHERE user_id = %s",
                    (user_id,)
                )
            data_rows = cur.fetchall()
        if not data_rows:
            return jsonify({'message': 'orders not found'}), 200
        return jsonify(data_rows), 200
    except Exception:
        return jsonify({'message': 'my fail'}), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
