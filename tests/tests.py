import pytest
import warnings
import requests

warnings.filterwarnings("ignore", category=pytest.PytestReturnNotNoneWarning)

from auth_tests import (
    gen_users,
    register_user,
    login_user,
    verify_user,
    logout_user,
    test_rate_limiting,
    test_duplicate_registration,
    test_invalid_login,
    User,
)
from users_tests import (
    user_info,
    user_change_username,
    user_change_email,
    users_list,
    user_delete,
    test_access_another_user,
    test_update_without_fields,
    test_duplicate_username,
)
from orders_tests import (
    create_order,
    get_order,
    get_user_orders,
    update_order_status,
    delete_order,
    test_create_order_invalid_amount,
    test_access_another_users_order,
)

users = gen_users(5)


@pytest.mark.parametrize("user", users)
class TestUserFlow:
    def test_register(self, user):
        assert register_user(user)

    def test_login(self, user):
        assert login_user(user)

    def test_verify(self, user):
        assert verify_user(user)

    def test_users_list(self, user):
        assert users_list(user)

    def test_user_info(self, user):
        assert user_info(user)

    def test_change_username(self, user):
        assert user_change_username(user)

    def test_change_email(self, user):
        assert user_change_email(user)

    def test_create_order(self, user):
        order_id = create_order(user)
        assert order_id is not False
        assert isinstance(order_id, int)

    def test_get_order(self, user):
        order_id = create_order(user)
        assert order_id is not False

        order = get_order(user, order_id)
        assert order is not False
        assert order.get("user_id") == user.user_id

    def test_get_user_orders(self, user):

        for _ in range(3):
            create_order(user)

        orders = get_user_orders(user, user.user_id)
        assert orders is not False
        assert len(orders) >= 3

    def test_update_order_status(self, user):
        order_id = create_order(user)
        assert order_id is not False

        assert update_order_status(user, order_id, "processing")
        assert update_order_status(user, order_id, "shipped")

    def test_delete_order(self, user):
        order_id = create_order(user)
        assert order_id is not False

        assert delete_order(user, order_id)

    def test_delete_user(self, user):
        assert user_delete(user)


class TestEdgeCases:
    def test_rate_limiting(self):
        result = test_rate_limiting()
        assert result, "Rate limiting should trigger after 10 attempts"

    def test_duplicate_registration(self):
        assert test_duplicate_registration()

    def test_invalid_login(self):
        assert test_invalid_login()

    def test_access_another_user(self):
        assert test_access_another_user()

    def test_update_without_fields(self):
        assert test_update_without_fields()

    def test_duplicate_username(self):
        assert test_duplicate_username()

    def test_create_order_invalid_amount(self):
        assert test_create_order_invalid_amount()

    def test_access_another_users_order(self):
        assert test_access_another_users_order()


class TestLogout:
    def test_logout(self):
        user = gen_users(1)[0]
        assert register_user(user)
        assert login_user(user)
        assert verify_user(user)

        assert logout_user(user)

        cookies = {"access_token": user.token}
        response = requests.post(
                "http://localhost:80/api/auth/verify", cookies=cookies, timeout=10
        )
        assert response.status_code == 401

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
