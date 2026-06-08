import os
from dotenv import load_dotenv
from functools import wraps
import logging

from flask import Flask, request, jsonify, g
import requests

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

app = Flask(__name__)
load_dotenv()


FLASK_MODE = os.getenv("FLASK_MOD", "dev")

if FLASK_MODE == "prod":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        filename="logs/app.log",
    )
else:
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
    )


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        cursor_factory=RealDictCursor,
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


def get_client_ip(request):
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr


def check_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.cookies.get("access_token")
        cli_ip = get_client_ip(request)

        if not token:
            app.logger.warning(
                f"WARNING [401] ip: {cli_ip} - Missing token for {request.method} {request.path}"
            )
            return jsonify({"error": "Authentication required"}), 401

        try:
            response = requests.post(
                "http://auth:5001/verify",
                cookies={"access_token": token},
                timeout=5,
            )

            if response.status_code != 200:
                app.logger.warning(
                    f"WARNING [401] ip: {cli_ip} - Invalid token for {request.method} {request.path}"
                )
                return jsonify({"error": "Invalid or expired token"}), 401

            user_data = response.json()
            g.user_id = user_data.get("user_id")

            app.logger.info(
                f"INFO [200] ip: {cli_ip} user_id: {g.user_id} - Token verified for {request.method} {request.path}"
            )

            return func(*args, **kwargs)

        except requests.exceptions.ConnectionError:
            app.logger.error(
                f"ERROR [503] ip: {cli_ip} - Cannot connect to auth_service for {request.path}"
            )
            return jsonify({"error": "Authentication service unavailable"}), 503
        except requests.exceptions.Timeout:
            app.logger.error(
                f"ERROR [504] ip: {cli_ip} - Auth service timeout for {request.path}"
            )
            return jsonify({"error": "Authentication service timeout"}), 504
        except requests.exceptions.RequestException as e:
            app.logger.error(
                f"ERROR [401] ip: {cli_ip} - Auth service request error: {str(e)}"
            )
            return jsonify({"error": "Authentication failed"}), 401
        except Exception as e:
            app.logger.error(
                f"ERROR [500] ip: {cli_ip} - Unexpected error in check_token: {str(e)}"
            )
            return jsonify({"error": "Internal server error"}), 500

    return wrapper


@app.route("/", methods=["POST"])
@check_token
def create_order():
    data = request.get_json()
    cli_ip = get_client_ip(request)
    if not data:
        app.logger.warning(
            f"WARNING [400] ip: {cli_ip} user_id: {g.user_id} - No JSON body"
        )
        return jsonify({"error": "Request body is required"}), 400

    order_name = data.get("order_name")
    total_amount = data.get("total_amount")

    if total_amount is None:
        app.logger.warning(
            f"WARNING [400] ip: {cli_ip} user_id: {g.user_id} - total_amount is required"
        )
        return jsonify({"error": "total_amount is required"}), 400

    if not order_name or order_name.strip() == "":
        app.logger.warning(
        )
        return jsonify({"error": "order name is empty"}), 400
    try:
        total_amount = int(total_amount)
        if total_amount < 1:
            app.logger.warning(
                f"WARNING [400] ip: {cli_ip} user_id: {g.user_id} - Invalid total_amount: {total_amount} (must be >= 1)"
            )
            return jsonify({"error": "total_amount must be at least 1"}), 400
    except (TypeError, ValueError):
        app.logger.warning(
            f"WARNING [400] ip: {cli_ip} user_id: {g.user_id} - total_amount type error: {total_amount}"
        )
        return jsonify({"error": "total_amount must be a valid integer"}), 400

    try:
        with get_db_cursor() as cur:
            cur.execute(
                "INSERT INTO orders (user_id, order_name, total_amount, status) VALUES (%s, %s, %s, 'pending') RETURNING id",
                (g.user_id, order_name, total_amount),
            )
            order_id = cur.fetchone()["id"]

        app.logger.info(
            f"INFO [201] ip: {cli_ip} user_id: {g.user_id} - Order created successfully, order_id: {order_id}, amount: {total_amount}"
        )
        return (
            jsonify({"message": "Order created successfully", "order_id": order_id}),
            201,
        )
    except psycopg2.Error as e:
        app.logger.error(
            f"ERROR [500] ip: {cli_ip} user_id: {g.user_id} - Database error creating order: {str(e)}"
        )
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        app.logger.error(
            f"ERROR [500] ip: {cli_ip} user_id: {g.user_id} - Unexpected error creating order: {str(e)}"
        )
        return jsonify({"error": "Internal server error"}), 500


@app.route("/<order_id>", methods=["GET"])
@check_token
def get_order(order_id):
    cli_ip = get_client_ip(request)
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
            data_row = cur.fetchone()
            if not data_row:
                app.logger.warning(
                    f"WARNING [404] ip: {cli_ip} user_id: {g.user_id} - Order not found: {order_id}"
                )
                return jsonify({"error": "Order not found"}), 404

            if data_row["user_id"] != g.user_id:
                app.logger.warning(
                    f"WARNING [403] ip: {cli_ip} user_id: {g.user_id} - Access denied to order {order_id} (owner: {data_row['user_id']})"
                )
                return jsonify({"error": "Access denied"}), 403

            app.logger.info(
                f"INFO [200] ip: {cli_ip} user_id: {g.user_id} - Retrieved order {order_id}"
            )
            return jsonify(data_row), 200
    except psycopg2.Error as e:
        app.logger.error(
            f"ERROR [500] ip: {cli_ip} user_id: {g.user_id} - Database error getting order {order_id}: {str(e)}"
        )
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        app.logger.error(
            f"ERROR [500] ip: {cli_ip} user_id: {g.user_id} - Unexpected error getting order {order_id}: {str(e)}"
        )
        return jsonify({"error": "Internal server error"}), 500


@app.route("/user/<user_id>", methods=["GET"])
@check_token
def get_users_orders(user_id):
    cli_ip = get_client_ip(request)
    try:
        if int(user_id) != g.user_id:
            app.logger.warning(
                f"WARNING [403] ip: {cli_ip} user_id: {g.user_id} - Access denied to view orders of user {user_id}"
            )
            return (
                jsonify({"error": "Access denied. You can only view your own orders."}),
                403,
            )

        with get_db_cursor() as cur:
            cur.execute(
                "SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
            data_rows = cur.fetchall()

        app.logger.info(
            f"INFO [200] ip: {cli_ip} user_id: {g.user_id} - Retrieved {len(data_rows)} orders for user {user_id}"
        )
        return jsonify(data_rows), 200
    except psycopg2.Error as e:
        app.logger.error(
            f"ERROR [500] ip: {cli_ip} user_id: {g.user_id} - Database error getting user orders: {str(e)}"
        )
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        app.logger.error(
            f"ERROR [500] ip: {cli_ip} user_id: {g.user_id} - Unexpected error getting user orders: {str(e)}"
        )
        return jsonify({"error": "Internal server error"}), 500


@app.route("/<order_id>", methods=["PUT"])
@check_token
def change_order_status(order_id):
    cli_ip = get_client_ip(request)
    data = request.get_json()
    if not data:
        app.logger.warning(
            f"WARNING [400] ip: {cli_ip} user_id: {g.user_id} - No JSON body for status update"
        )
        return jsonify({"error": "Request body is required"}), 400

    status = data.get("status")
    valid_statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]

    if not status:
        app.logger.warning(
            f"WARNING [400] ip: {cli_ip} user_id: {g.user_id} - status field is required"
        )
        return jsonify({"error": "status is required"}), 400

    if status not in valid_statuses:
        app.logger.warning(
            f"WARNING [400] ip: {cli_ip} user_id: {g.user_id} - Invalid status: {status}, allowed: {valid_statuses}"
        )
        return (
            jsonify(
                {
                    "error": f'Invalid status. Allowed values: {", ".join(valid_statuses)}'
                }
            ),
            400,
        )

    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
            order = cur.fetchone()

            if not order:
                app.logger.warning(
                    f"WARNING [404] ip: {cli_ip} user_id: {g.user_id} - Order {order_id} not found for status update"
                )
                return jsonify({"error": "Order not found"}), 404

            if order["user_id"] != g.user_id:
                app.logger.warning(
                    f"WARNING [403] ip: {cli_ip} user_id: {g.user_id} - Access denied to update order {order_id}"
                )
                return jsonify({"error": "Access denied"}), 403

            cur.execute(
                "UPDATE orders SET status = %s WHERE id = %s", (status, order_id)
            )

            app.logger.info(
                f"INFO [200] ip: {cli_ip} user_id: {g.user_id} - Order {order_id} status changed from {order['status']} to {status}"
            )
            return jsonify({"message": "Order status updated successfully"}), 200
    except psycopg2.Error as e:
        app.logger.error(
            f"ERROR [500] ip: {cli_ip} user_id: {g.user_id} - Database error updating order {order_id}: {str(e)}"
        )
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        app.logger.error(
            f"ERROR [500] ip: {cli_ip} user_id: {g.user_id} - Unexpected error updating order {order_id}: {str(e)}"
        )
        return jsonify({"error": "Internal server error"}), 500


@app.route("/<order_id>", methods=["DELETE"])
@check_token
def delete_order(order_id):
    cli_ip = get_client_ip(request)
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
            order = cur.fetchone()

            if not order:
                app.logger.warning(
                    f"WARNING [404] ip: {cli_ip} user_id: {g.user_id} - Order {order_id} not found for deletion"
                )
                return jsonify({"error": "Order not found"}), 404

            if order["user_id"] != g.user_id:
                app.logger.warning(
                    f"WARNING [403] ip: {cli_ip} user_id: {g.user_id} - Access denied to delete order {order_id}"
                )
                return jsonify({"error": "Access denied"}), 403

            cur.execute("DELETE FROM orders WHERE id = %s", (order_id,))

            app.logger.info(
                f"INFO [204] ip: {cli_ip} user_id: {g.user_id} - Order {order_id} deleted successfully"
            )
            return "", 204
    except psycopg2.Error as e:
        app.logger.error(
            f"ERROR [500] ip: {cli_ip} user_id: {g.user_id} - Database error deleting order {order_id}: {str(e)}"
        )
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        app.logger.error(
            f"ERROR [500] ip: {cli_ip} user_id: {g.user_id} - Unexpected error deleting order {order_id}: {str(e)}"
        )
        return jsonify({"error": "Internal server error"}), 500


@app.route("/health", methods=["GET"])
def health():
    cli_ip = get_client_ip(request)
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT 1")
        app.logger.info(f"INFO [200] ip: {cli_ip} - Health check passed")
        return jsonify({"status": "healthy"}), 200
    except psycopg2.Error as e:
        app.logger.error(
            f"ERROR [503] ip: {cli_ip} - Health check failed - Database error: {str(e)}"
        )
        return (
            jsonify({"status": "unhealthy", "message": "Database connection failed"}),
            503,
        )
    except Exception as e:
        app.logger.error(f"ERROR [503] ip: {cli_ip} - Health check failed: {str(e)}")

        return jsonify({"status": "unhealthy", "message": str(e)}), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
