import random 
import string
import pytest
import requests

def test_register():
    for user in users:
        data = {
                'username': user.username,
                'email': user.email,
                'password': user.password
            }
        response = requests.post(
                'http://localhost:5001/requests',
                headers={'Content-Type': 'application/json'},
                json=data
            )
        assert response.status_code == 200

class User:
    def __init__(self):
        self.username = 'default'
        self.email = 'default'
        self.password = 'default'
        self.letters = string.ascii_lowercase + string.digits
    
    def random_user(self):
        """ Generate random user """
        self.username = self._gen_username()
        self.email = self._gen_email()
        self.password = self._gen_password()
        return self

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
