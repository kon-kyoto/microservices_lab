import pytest
from auth_tests import gen_users, register_user, login_user, verify_user
from users_tests import user_info, user_change_username, user_change_email, users_list, user_delete

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
    
    def test_delete(self, user):
        assert user_delete(user)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
