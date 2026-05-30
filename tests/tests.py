import pytest
from auth_tests import gen_users, register_user, login_user, verify_user

users = gen_users()

@pytest.mark.parametrize("user", users)
def tests(user):
    assert register_user(user)
    assert login_user(user)
    assert verify_user(user)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
