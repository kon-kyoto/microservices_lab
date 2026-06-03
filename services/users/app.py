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

JWT_CONFIG = {
    "algorithm": "HS256",
    "secret_key": os.getenv("SECRET_KEY"),
    "expires_hours": int(os.getenv("TIMEDELTA", "24")),
}


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
                "http://auth_service:5001/verify",
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


@app.route("/<find_id>", methods=["GET"])
@check_token
def get_user(find_id):
    user_id = g.get("user_id")
    cli_ip = get_client_ip(request)

    if str(user_id) != str(find_id):
        app.logger.warning(
            f"WARNING [403] ip: {cli_ip} user_id: {user_id} - Access denied to view user {find_id}"
        )
        return (
            jsonify({"error": "Access denied. You can only access your own profile."}),
            403,
        )

    try:
        with get_db_cursor() as cur:
            cur.execute(
                "SELECT id, username, email, created_at FROM users WHERE id = %s",
                (find_id,),
            )
            data_row = cur.fetchone()
            if not data_row:
                app.logger.warning(
                    f"WARNING [404] ip: {cli_ip} user_id: {user_id} - User {find_id} not found"
                )
                return jsonify({"error": "User not found"}), 404

        app.logger.info(
            f"INFO [200] ip: {cli_ip} user_id: {user_id} - Retrieved user profile for {find_id}"
        )
        return (
            jsonify(
                {
                    "username": data_row.get("username"),
                    "email": data_row.get("email"),
                    "created_at": data_row.get("created_at"),
                }
            ),
            200,
        )
    except psycopg2.Error as e:
        app.logger.error(
            f"ERROR [500] ip: {cli_ip} user_id: {user_id} - Database error getting user {find_id}: {str(e)}"
        )
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        app.logger.error(
            f"ERROR [500] ip: {cli_ip} user_id: {user_id} - Unexpected error getting user {find_id}: {str(e)}"
        )
        return jsonify({"error": "Internal server error"}), 500


@app.route("/<find_id>", methods=["PUT"])
@check_token
def user_change(find_id):
    data = request.get_json()
    cli_ip = get_client_ip(request)
    if not data:
        app.logger.warning(
            f"WARNING [400] ip: {cli_ip} user_id: {g.user_id} - No JSON body for update"
        )
        return jsonify({"error": "Request body is required"}), 400

    username = data.get("username")
    email = data.get("email")
    user_id = g.get("user_id")

    if str(user_id) != str(find_id):
        app.logger.warning(
            f"WARNING [403] ip: {cli_ip} user_id: {user_id} - Access denied to modify user {find_id}"
        )
        return (
            jsonify({"error": "Access denied. You can only modify your own profile."}),
            403,
        )

    if not username and not email:
        app.logger.warning(
            f"WARNING [400] ip: {cli_ip} user_id: {user_id} - No fields to update"
        )
        return (
            jsonify(
                {
                    "error": "At least one field (username or email) is required for update"
                }
            ),
            400,
        )

    try:
        with get_db_cursor() as cur:
            if email:
                # Проверка, что email не занят другим пользователем
                cur.execute(
                    "SELECT id FROM users WHERE email = %s AND id != %s",
                    (email, user_id),
                )
                if cur.fetchone():
                    app.logger.warning(
                        f"WARNING [409] ip: {cli_ip} user_id: {user_id} - Email {email} already in use"
                    )
                    return jsonify({"error": "Email already in use"}), 409

                cur.execute(
                    "UPDATE users SET email = %s WHERE id = %s", (email, user_id)
                )
                app.logger.info(
                    f"INFO [200] ip: {cli_ip} user_id: {user_id} - Email updated to {email}"
                )

            if username:
                # Проверка, что username не занят другим пользователем
                cur.execute(
                    "SELECT id FROM users WHERE username = %s AND id != %s",
                    (username, user_id),
                )
                if cur.fetchone():
                    app.logger.warning(
                        f"WARNING [409] ip: {cli_ip} user_id: {user_id} - Username {username} already taken"
                    )
                    return jsonify({"error": "Username already taken"}), 409

                cur.execute(
                    "UPDATE users SET username = %s WHERE id = %s", (username, user_id)
                )
                app.logger.info(
                    f"INFO [200] ip: {cli_ip} user_id: {user_id} - Username updated to {username}"
                )

        app.logger.info(
            f"INFO [200] ip: {cli_ip} user_id: {user_id} - Profile updated successfully"
        )
        return jsonify({"message": "Profile updated successfully"}), 200
    except psycopg2.Error as e:
        app.logger.error(
            f"ERROR [500] ip: {cli_ip} user_id: {user_id} - Database error updating user: {str(e)}"
        )
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        app.logger.error(
            f"ERROR [500] ip: {cli_ip} user_id: {user_id} - Unexpected error updating user: {str(e)}"
        )
        return jsonify({"error": "Internal server error"}), 500


@app.route("/<find_id>", methods=["DELETE"])
@check_token
def user_delete(find_id):
    user_id = g.get("user_id")
    cli_ip = get_client_ip(request)

    if str(user_id) != str(find_id):
        app.logger.warning(
            f"WARNING [403] ip: {cli_ip} user_id: {user_id} - Access denied to delete user {find_id}"
        )
        return (
            jsonify({"error": "Access denied. You can only delete your own account."}),
            403,
        )

    try:
        with get_db_cursor() as cur:
            # Проверяем, существует ли пользователь
            cur.execute("SELECT id FROM users WHERE id = %s", (find_id,))
            if not cur.fetchone():
                app.logger.warning(
                    f"WARNING [404] ip: {cli_ip} user_id: {user_id} - User {find_id} not found for deletion"
                )
                return jsonify({"error": "User not found"}), 404

            # Удаляем связанные записи в auth_users
            cur.execute("DELETE FROM auth_users WHERE user_id = %s", (find_id,))
            # Удаляем пользователя
            cur.execute("DELETE FROM users WHERE id = %s", (find_id,))

        app.logger.info(
            f"INFO [204] ip: {cli_ip} user_id: {user_id} - Account deleted successfully"
        )
        return "", 204
    except psycopg2.Error as e:
        app.logger.error(
            f"ERROR [500] ip: {cli_ip} user_id: {user_id} - Database error deleting user: {str(e)}"
        )
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        app.logger.error(
            f"ERROR [500] ip: {cli_ip} user_id: {user_id} - Unexpected error deleting user: {str(e)}"
        )
        return jsonify({"error": "Internal server error"}), 500


@app.route("/", methods=["GET"])
@check_token
def users_list():
    user_id = g.get("user_id")
    cli_ip = get_client_ip(request)

    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT id, username, email, created_at FROM users ORDER BY id")
            data = cur.fetchall()

        app.logger.info(
            f"INFO [200] ip: {cli_ip} user_id: {user_id} - Retrieved {len(data)} users list"
        )
        return jsonify(data), 200
    except psycopg2.Error as e:
        app.logger.error(
            f"ERROR [500] ip: {cli_ip} user_id: {user_id} - Database error getting users list: {str(e)}"
        )
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        app.logger.error(
            f"ERROR [500] ip: {cli_ip} user_id: {user_id} - Unexpected error getting users list: {str(e)}"
        )
        return jsonify({"error": "Internal server error"}), 500


@app.route("/health", methods=["GET"])
def health():
    try:
        cli_ip = get_client_ip(request)
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
    app.run(host="0.0.0.0", port=5002)
