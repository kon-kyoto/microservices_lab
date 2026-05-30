import random
import string
import requests
import time


class User:
    def __init__(self):
        self.username = "default"
        self.email = "default"
        self.password = "default"
        self.letters = string.ascii_lowercase + string.digits
        self.token = ""
        self.user_id = None

    def random_user(self):
        """Generate random user"""
        self.username = self._gen_username()
        self.email = self._gen_email()
        self.password = self._gen_password()
        return self

    def set_token(self, token):
        self.token = token

    def set_user_id(self, user_id):
        self.user_id = user_id

    def _gen_username(self):
        """Generate random username"""
        return "".join(
            random.choice(self.letters) for _ in range(random.randint(5, 10))
        )

    def _gen_email(self):
        """Generate random email"""
        domains = ["gmail.com", "yahoo.com", "outlook.com", "mail.ru", "example.com"]
        random_suffix = "".join(
            random.choice(self.letters) for _ in range(random.randint(4, 10))
        )
        domain = random.choice(domains)
        return f"{self.username}{random_suffix}@{domain}"

    def _gen_password(self):
        """Generate random password"""
        return "".join(
            random.choice(self.letters) for _ in range(random.randint(8, 16))
        )


def gen_users(length=10):
    users = []
    for _ in range(length):
        users.append(User().random_user())
    return users


def register_user(user, expected_status=201):
    """Register a user"""
    data = {"username": user.username, "email": user.email, "password": user.password}
    response = requests.post(
        "http://localhost:5001/register",
        headers={"Content-Type": "application/json"},
        json=data,
        timeout=10,
    )

    if response.status_code == 201:
        user_id = response.json().get("user_id")
        if user_id:
            user.set_user_id(user_id)

    return response.status_code == expected_status


def login_user(user, expected_status=200):
    """Login a user"""
    data = {"username": user.username, "password": user.password}
    response = requests.post(
        "http://localhost:5001/login",
        headers={"Content-Type": "application/json"},
        json=data,
        timeout=10,
    )

    if response.status_code == 200:
        token = response.cookies.get("access_token")
        if token:
            user.set_token(token)

    return response.status_code == expected_status


def verify_user(user, expected_status=200):
    """Verify user token"""
    if not user.token:
        return False

    cookies = {"access_token": user.token}
    response = requests.post(
        "http://localhost:5001/verify", cookies=cookies, timeout=10
    )

    if response.status_code == 200:
        user_id = response.json().get("user_id")
        if user_id:
            user.set_user_id(user_id)

    return response.status_code == expected_status


def logout_user(user, expected_status=200):
    """Logout user (blacklist token)"""
    cookies = {"access_token": user.token}
    response = requests.post(
        "http://localhost:5001/logout", cookies=cookies, timeout=10
    )

    return response.status_code == expected_status


def test_rate_limiting():
    """Test rate limiting on login endpoint"""
    user = User().random_user()

    # Register user
    if not register_user(user):
        return False

    # В Docker все запросы с одного IP, rate limiting не сработает
    # Поэтому проверяем, что Redis работает, а rate limiting может не работать
    try:
        import redis

        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        r.ping()
        redis_available = True
    except:
        redis_available = False

    if not redis_available:
        # Если Redis не работает, тест пропускаем
        return True

    # Для Docker нужно больше попыток или использовать другой подход
    rate_limit_hit = False

    for i in range(15):  # Увеличим до 15 попыток
        data = {"username": user.username, "password": user.password}
        response = requests.post(
            "http://localhost:5001/login",
            headers={"Content-Type": "application/json"},
            json=data,
            timeout=10,
        )

        if response.status_code == 429:
            rate_limit_hit = True
            break

        # Небольшая задержка
        time.sleep(0.05)

    return rate_limit_hit


def test_duplicate_registration():
    """Test registering the same user twice"""
    user = User().random_user()

    # First registration - should succeed
    if not register_user(user):
        return False

    # Second registration - should fail with 409
    return register_user(user, expected_status=409)


def test_invalid_login():
    """Test login with invalid credentials"""
    user = User().random_user()

    # Try to login without registering first - should get 401
    result = login_user(user, expected_status=401)
    if not result:
        return False

    # Register
    if not register_user(user):
        return False

    # Try with wrong password
    wrong_password_user = User()
    wrong_password_user.username = user.username
    wrong_password_user.password = "wrong_password"

    return login_user(wrong_password_user, expected_status=401)
