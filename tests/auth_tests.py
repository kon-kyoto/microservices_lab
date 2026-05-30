import random 
import string
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

def gen_users(length=10):
    users = []
    for _ in range(length):
        users.append(User().random_user())
    
    return users


def register_user(user):
    data = {
        'username': user.username,
        'email': user.email,
        'password': user.password
    }
    response = requests.post(
        'http://localhost:5001/register',
        headers={'Content-Type': 'application/json'},
        json=data
    )
    return response.status_code == 201

def login_user(user):
    data = {
        'username': user.username,
        'password': user.password
    }
    response = requests.post(
        'http://localhost:5001/login',
        headers={'Content-Type': 'application/json'},
        json=data
    )
    
    user.set_token(response.cookies.get('access_token'))

    return response.status_code == 200

def verify_user(user):
    data = {
            'access_token': user.token
        }
    response = requests.post(
            'http://localhost:5001/verify',
            cookies=data
        )

    return response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
