import requests
import random
from auth_tests import User, register_user, login_user, verify_user


def create_order(user, total_amount=None, order_name=None, expected_status=201):
    """Create an order with optional name"""
    if not user.token:
        return False

    if total_amount is None:
        total_amount = random.randint(1, 10000)

    if order_name is None:
        order_name = f"Test Order {random.randint(1, 9999)}"

    cookie = {"access_token": user.token}
    data = {"total_amount": total_amount, "order_name": order_name}

    response = requests.post(
        "http://localhost:80/api/orders/",
        headers={"Content-Type": "application/json"},
        cookies=cookie,
        json=data,
        timeout=10,
    )

    if response.status_code == 201:
        order_id = response.json().get("order_id")
        return order_id

    return response.status_code == expected_status


def get_order(user, order_id, expected_status=200):
    """Get order by ID"""
    if not user.token:
        return False

    cookie = {"access_token": user.token}
    response = requests.get(
        f"http://localhost:80/api/orders/{order_id}", cookies=cookie, timeout=10
    )

    if response.status_code == 200:
        return response.json()

    return response.status_code == expected_status


def get_user_orders(user, user_id, expected_status=200):
    """Get all orders for a user"""
    if not user.token:
        return False

    cookie = {"access_token": user.token}
    response = requests.get(
        f"http://localhost:80/api/orders/user/{user_id}", cookies=cookie, timeout=10
    )

    if response.status_code == 200:
        return response.json()

    return response.status_code == expected_status


def update_order_status(user, order_id, status, expected_status=200):
    """Update order status"""
    if not user.token:
        return False

    valid_statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
    if status not in valid_statuses:
        return False

    cookie = {"access_token": user.token}
    data = {"status": status}

    response = requests.put(
        f"http://localhost:80/api/orders/{order_id}",
        headers={"Content-Type": "application/json"},
        cookies=cookie,
        json=data,
        timeout=10,
    )

    return response.status_code == expected_status


def delete_order(user, order_id, expected_status=204):
    """Delete an order"""
    if not user.token:
        return False

    cookie = {"access_token": user.token}
    response = requests.delete(
        f"http://localhost:80/api/orders/{order_id}", cookies=cookie, timeout=10
    )

    return response.status_code == expected_status


def test_create_order_invalid_amount():
    """Test creating order with invalid amount"""
    user = User().random_user()

    if not register_user(user):
        return False
    if not login_user(user):
        return False
    if not verify_user(user):
        return False

    cookie = {"access_token": user.token}

    # ✅ Тест с неверным форматом суммы
    response = requests.post(
        "http://localhost:80/api/orders/",
        headers={"Content-Type": "application/json"},
        cookies=cookie,
        json={
            "total_amount": "not_a_number",
            "order_name": "Test Order",  # ✅ Добавлено поле
        },
        timeout=10,
    )

    return response.status_code == 405


def test_create_order_without_name():
    """Test creating order without order_name (should fail)"""
    user = User().random_user()

    if not register_user(user):
        return False
    if not login_user(user):
        return False
    if not verify_user(user):
        return False

    cookie = {"access_token": user.token}

    # ✅ Тест без order_name
    response = requests.post(
        "http://localhost:80/api/orders/",
        headers={"Content-Type": "application/json"},
        cookies=cookie,
        json={"total_amount": 1000},
        timeout=10,
    )

    return (
        response.status_code == 400
    )  # Должен вернуть 400, так как order_name обязателен


def test_create_order_with_empty_name():
    """Test creating order with empty order_name (should fail)"""
    user = User().random_user()

    if not register_user(user):
        return False
    if not login_user(user):
        return False
    if not verify_user(user):
        return False

    cookie = {"access_token": user.token}

    # ✅ Тест с пустым order_name
    response = requests.post(
        "http://localhost:80/api/orders/",
        headers={"Content-Type": "application/json"},
        cookies=cookie,
        json={"total_amount": 1000, "order_name": ""},
        timeout=10,
    )

    return response.status_code == 400


def test_access_another_users_order():
    """Test that user1 cannot access user2's order"""
    user1 = User().random_user()
    user2 = User().random_user()

    if not register_user(user1):
        return False
    if not login_user(user1):
        return False
    if not verify_user(user1):
        return False

    if not register_user(user2):
        return False
    if not login_user(user2):
        return False
    if not verify_user(user2):
        return False

    # Create order for user2
    order_id = create_order(user2)
    if not order_id:
        return False

    # Try to access with user1's token
    cookie = {"access_token": user1.token}
    response = requests.get(
        f"http://localhost:80/api/orders/{order_id}", cookies=cookie, timeout=10
    )

    return response.status_code == 403


def test_order_has_name_field():
    """Test that order response includes order_name field"""
    user = User().random_user()

    if not register_user(user):
        return False
    if not login_user(user):
        return False
    if not verify_user(user):
        return False

    # Create order with specific name
    test_name = f"Test Order {random.randint(1, 9999)}"
    order_id = create_order(user, total_amount=1000, order_name=test_name)

    if not order_id:
        return False

    # Get order and check name field
    order = get_order(user, order_id)

    if not order or not isinstance(order, dict):
        return False

    # ✅ Проверяем наличие поля order_name
    if "order_name" not in order:
        return False

    # ✅ Проверяем, что имя соответствует созданному
    return order.get("order_name") == test_name
