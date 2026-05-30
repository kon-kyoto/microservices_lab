import pytest
from auth_tests import gen_users, register_user, login_user, verify_user
from users_tests import user_info, user_change_username, user_change_email, users_list, user_delete

users = gen_users()

@pytest.mark.parametrize("user", users)
def tests(user):
    assert register_user(user)
    assert login_user(user)
    assert verify_user(user)
    assert users_list(user)
    assert user_info(user)
    assert user_change_username(user)
    assert user_change_email(user)
    assert user_delete(user)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
