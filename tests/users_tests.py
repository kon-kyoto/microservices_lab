import requests
import random
import string
from auth_tests import User, register_user, login_user, verify_user

letters = string.ascii_lowercase + string.digits


def user_info(user, expected_status=200):
    """Get user information"""
    if not user.token:
        return False

    cookie = {"access_token": user.token}
    response = requests.get(
        f"http://localhost:80/api/users/{user.user_id}", cookies=cookie, timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        return data.get("username") == user.username and data.get("email") == user.email

    return response.status_code == expected_status


def user_change_username(user, expected_status=200):
    """Change username"""
    if not user.token:
        return False

    new_username = user.username + "".join(random.choice(letters) for _ in range(3))
    cookie = {"access_token": user.token}

    response = requests.put(
        f"http://localhost:80/api/users/{user.user_id}",
        headers={"Content-Type": "application/json"},
        cookies=cookie,
        json={"username": new_username},
        timeout=10,
    )

    if response.status_code == 200:
        user.username = new_username
        return True

    return response.status_code == expected_status


def user_change_email(user, expected_status=200):
    """Change email"""
    if not user.token:
        return False

    new_email = f"{user.username}_{random.randint(1, 9999)}@test.com"
    cookie = {"access_token": user.token}

    response = requests.put(
        f"http://localhost:80/api/users/{user.user_id}",
        headers={"Content-Type": "application/json"},
        cookies=cookie,
        json={"email": new_email},
        timeout=10,
    )

    if response.status_code == 200:
        user.email = new_email
        return True

    return response.status_code == expected_status


def users_list(user, expected_status=200):
    """Get list of all users"""
    if not user.token:
        return False

    cookie = {"access_token": user.token}
    response = requests.get("http://localhost:80/api/users/", cookies=cookie, timeout=10)

    if response.status_code == 200:
        data = response.json()
        return isinstance(data, list)

    return response.status_code == expected_status


def user_delete(user, expected_status=204):
    """Delete user account"""
    if not user.token:
        return False

    cookie = {"access_token": user.token}
    response = requests.delete(
        f"http://localhost:80/api/users/{user.user_id}", cookies=cookie, timeout=10
    )

    return response.status_code == expected_status


def test_access_another_user():
    """Test that user1 cannot access user2's data"""
    user1 = User().random_user()
    user2 = User().random_user()

    # Create and login both users
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

    # Try to access user2's data with user1's token
    cookie = {"access_token": user1.token}
    response = requests.get(
        f"http://localhost:80/api/users/{user2.user_id}", cookies=cookie, timeout=10
    )

    return response.status_code == 403


def test_update_without_fields():
    """Test update user without providing any fields"""
    user = User().random_user()

    if not register_user(user):
        return False
    if not login_user(user):
        return False
    if not verify_user(user):
        return False

    cookie = {"access_token": user.token}
    response = requests.put(
        f"http://localhost:80/api/users/{user.user_id}",
        headers={"Content-Type": "application/json"},
        cookies=cookie,
        json={},
        timeout=10,
    )

    return response.status_code == 400


def test_duplicate_username():
    """Test using duplicate username"""
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

    # Try to change user2's username to user1's username
    cookie = {"access_token": user2.token}
    response = requests.put(
        f"http://localhost:80/api/users/{user2.user_id}",
        headers={"Content-Type": "application/json"},
        cookies=cookie,
        json={"username": user1.username},
        timeout=10,
    )

    return response.status_code == 409
