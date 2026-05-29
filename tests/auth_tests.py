import random 
import string
import pytest
import requests

class User:
    def __init__(self):
        self.username = 'default'
        self.email = 'default'
        self.password = 'default'
        self.letters = string.ascii_lowercase + string.digits
        self.token = ''
    
    def random_user(self):
        """ Generate random user """
        self.username = self._gen_username()
        self.email = self._gen_email()
        self.password = self._gen_password()
        return self

    def set_token(self, token):
        self.token = token

    def _gen_username(self):
        """ Generate random username """
        return ''.join(random.choice(self.letters) for _ in range(random.randint(5, 10)))
    
    def _gen_email(self):
        """ Generate random email """
        domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'mail.ru', 'example.com']
        random_suffix = ''.join(random.choice(self.letters) for _ in range(random.randint(4, 10)))
        domain = random.choice(domains)
        return f"{self.username}{random_suffix}@{domain}"
    
    def _gen_password(self):
        """ Generate random password """
        return ''.join(random.choice(self.letters) for _ in range(random.randint(8, 16)))

users = []
def gen_users(length=10):
    for _ in range(length):
        users.append(User().random_user())

gen_users()

@pytest.mark.parametrize("user", users)
def test_register(user):
    data = { 'username': user.username,
        'email': user.email,
        'password': user.password
    }
    response = requests.post(
        'http://localhost:5001/register',
        headers={'Content-Type': 'application/json'},
        json=data
    )
    assert response.status_code == 201

@pytest.mark.parametrize("user", users)
def test_login(user):
    data = { 'username': user.username,
        'email': user.email,
        'password': user.password
    }
    response = requests.post(
        'http://localhost:5001/register',
        headers={'Content-Type': 'application/json'},
        json=data
    )
    
    user.set_token(response.cookies.get('access_token'))

    assert response.status_code == 200

@pytest.mark.parametrize("user", users)
def test_verify(user):
    data = {
            'access_token': user.token
        }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
