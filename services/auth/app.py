import os
from dotenv import load_dotenv
import re
import logging

from flask import Flask, request, make_response, jsonify
import redis

import bcrypt
import jwt
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

load_dotenv()
app = Flask(__name__)

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

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True,
)

JWT_CONFIG = {
    "algorithm": "HS256",
    "secret_key": os.getenv("SECRET_KEY"),
    "expires_hours": int(os.getenv("TIMEDELTA", "24")),
}


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


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    cli_ip = get_client_ip(request)
    if not data:
        app.logger.warning(f"WARNING [400] ip: {cli_ip} - Request body is required")
        return jsonify({"error": "Request body is required"}), 400

    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    if not username or not password or not email:
        app.logger.warning(f"WARNING [400] ip: {cli_ip} - Missing required fields")
        return (
            jsonify({"error": "Missing required fields: username, email, password"}),
            400,
        )

    email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(email_pattern, email):
        app.logger.warning(
            f"WARNING [400] ip: {cli_ip} - Invalid email format: {email}"
        )
        return jsonify({"error": "Invalid email format"}), 400

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    try:
        with get_db_cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, email) VALUES (%s, %s) RETURNING id",
                (username, email),
            )
            user_id = cur.fetchone()["id"]
            cur.execute(
                "INSERT INTO auth_users (user_id, password_hash) VALUES (%s, %s)",
                (user_id, password_hash.decode("utf-8")),
            )
            app.logger.info(
                f"INFO [201] ip: {cli_ip} user_id: {user_id} - User created successfully"
            )
            return (
                jsonify({"message": "User created successfully", "user_id": user_id}),
                201,
            )
    except psycopg2.IntegrityError:
        app.logger.warning(
            f"WARNING [409] ip: {cli_ip} - Username or email already exists: {username}/{email}"
        )
        return jsonify({"error": "Username or email already exists"}), 409
    except Exception as e:
        app.logger.error(f"ERROR [500] ip: {cli_ip} - Registration error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    cli_ip = get_client_ip(request)
    if not data:
        app.logger.warning(f"WARNING [400] ip: {cli_ip} - Request body is required")
        return jsonify({"error": "Request body is required"}), 400

    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    if not password:
        app.logger.warning(f"WARNING [400] ip: {cli_ip} - Password is required")
        return jsonify({"error": "Password is required"}), 400

    if not email and not username:
        app.logger.warning(
            f"WARNING [400] ip: {cli_ip} - Either email or username is required"
        )
        return jsonify({"error": "Either email or username is required"}), 400

    rate_key = f"login_rate:{cli_ip}"
    att = redis_client.incr(rate_key)
    if att == 1:
        redis_client.expire(rate_key, int(os.getenv("STOP_LOGIN", 300)))
    if att > 10:
        app.logger.warning(
            f"WARNING [429] ip: {cli_ip} - Too many login attempts (attempts: {att})"
        )
        return jsonify({"error": "Too many login attempts. Try again later."}), 429

    try:
        with get_db_cursor() as cur:
            if username:
                cur.execute(
                    "SELECT id FROM users WHERE username = %s LIMIT 1", (username,)
                )
            else:
                cur.execute("SELECT id FROM users WHERE email = %s LIMIT 1", (email,))

            user_row = cur.fetchone()
            if not user_row:
                app.logger.warning(
                    f"WARNING [401] ip: {cli_ip} - Invalid credentials - user not found"
                )
                return jsonify({"error": "Invalid credentials"}), 401

            user_id = user_row["id"]

            cur.execute(
                "SELECT password_hash FROM auth_users WHERE user_id = %s", (user_id,)
            )
            password_row = cur.fetchone()
            if not password_row:
                app.logger.warning(
                    f"WARNING [401] ip: {cli_ip} user_id: {user_id} - Invalid credentials - no password hash"
                )
                return jsonify({"error": "Invalid credentials"}), 401

            if not bcrypt.checkpw(
                password.encode("utf-8"), password_row["password_hash"].encode("utf-8")
            ):
                app.logger.warning(
                    f"WARNING [401] ip: {cli_ip} user_id: {user_id} - Invalid credentials - wrong password"
                )
                return jsonify({"error": "Invalid credentials"}), 401

        token = jwt.encode(
            {
                "user_id": user_id,
                "exp": datetime.utcnow() + timedelta(hours=JWT_CONFIG["expires_hours"]),
            },
            JWT_CONFIG["secret_key"],
            algorithm=JWT_CONFIG["algorithm"],
        )

        redis_client.delete(rate_key)

        response = make_response(
            jsonify({"message": "Login successful", "user_id": user_id})
        )

        secure_cookie = request.headers.get("X-Forwarded-Proto") == "https"
        response.set_cookie(
            "access_token",
            token,
            httponly=True,
            secure=secure_cookie,
            samesite="Lax",
            max_age=24 * 60 * 60,
        )
        app.logger.info(
            f"INFO [200] ip: {cli_ip} user_id: {user_id} - Login successful"
        )
        return response, 200

    except Exception as e:
        app.logger.error(f"ERROR [500] ip: {cli_ip} - Login error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/logout", methods=["POST"])
def logout():
    token = request.cookies.get("access_token")
    cli_ip = get_client_ip(request)

    if not token:
        app.logger.warning(f"WARNING [401] ip: {cli_ip} - No token provided for logout")
        return jsonify({"error": "No token provided"}), 401

    try:
        jwt_data = jwt.decode(
            token, JWT_CONFIG["secret_key"], algorithms=[JWT_CONFIG["algorithm"]]
        )
        user_id = jwt_data.get("user_id")
        exp_timestamp = jwt_data["exp"]
        current_time = datetime.utcnow().timestamp()
        ttl = int(exp_timestamp - current_time)

        if ttl > 0:
            redis_client.setex(f"blacklist:{token}", ttl, "revoked")
            app.logger.info(
                f"INFO [200] ip: {cli_ip} user_id: {user_id} - Logout successful, token blacklisted for {ttl} seconds"
            )
        else:
            app.logger.info(
                f"INFO [200] ip: {cli_ip} user_id: {user_id} - Logout successful, token already expired"
            )

        return jsonify({"message": "Logout completed"}), 200

    except jwt.ExpiredSignatureError:
        app.logger.warning(
            f"WARNING [401] ip: {cli_ip} - Logout attempt with expired token"
        )
        return jsonify({"error": "Token already expired"}), 401
    except jwt.InvalidTokenError:
        app.logger.warning(
            f"WARNING [401] ip: {cli_ip} - Logout attempt with invalid token"
        )
        return jsonify({"error": "Invalid token"}), 401
    except Exception as e:
        app.logger.error(f"ERROR [500] ip: {cli_ip} - Logout error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/verify", methods=["POST"])
def verify():
    token = request.cookies.get("access_token")
    cli_ip = get_client_ip(request)

    if not token:
        app.logger.warning(
            f"WARNING [401] ip: {cli_ip} - No token provided for verification"
        )
        return jsonify({"error": "No token provided"}), 401

    if redis_client.exists(f"blacklist:{token}"):
        app.logger.warning(f"WARNING [401] ip: {cli_ip} - Token has been revoked")
        return jsonify({"error": "Token has been revoked"}), 401

    try:
        jwt_data = jwt.decode(
            token, JWT_CONFIG["secret_key"], algorithms=[JWT_CONFIG["algorithm"]]
        )
        user_id = jwt_data.get("user_id")
        app.logger.info(
            f"INFO [200] ip: {cli_ip} user_id: {user_id} - Token verified successfully"
        )
        return jsonify({"valid": True, "user_id": user_id}), 200
    except jwt.ExpiredSignatureError:
        app.logger.warning(f"WARNING [401] ip: {cli_ip} - Token has expired")
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        app.logger.warning(f"WARNING [401] ip: {cli_ip} - Invalid token")
        return jsonify({"error": "Invalid token"}), 401
    except Exception as e:
        app.logger.error(f"ERROR [500] ip: {cli_ip} - Verify error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/health", methods=["GET"])
def health():
    try:
        cli_ip = get_client_ip(request)
        with get_db_cursor() as cur:
            cur.execute("SELECT 1")
            redis_client.ping()
        app.logger.info(f"INFO [200] ip: {cli_ip} - Health check passed")
        return jsonify({"status": "healthy"}), 200
    except redis.ConnectionError as e:
        app.logger.error(
            f"ERROR [503] ip: {cli_ip} - Health check failed - Redis error: {str(e)}"
        )
        return (
            jsonify({"status": "unhealthy", "message": "Redis connection failed"}),
            503,
        )
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
    app.run(host="0.0.0.0", port=5001)
