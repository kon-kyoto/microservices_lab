import pytest
from auth_tests import gen_users, test_register, test_login, test_verify

users = gen_users()

@pytest.mark.parametrize("user", users)
def tests(user):
    assert test_register(user)
    assert test_login(user)
    assert test_verify(user)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
