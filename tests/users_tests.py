import requests
import random
import string

letters = string.ascii_lowercase + string.digits

def user_info(user):
    cookie = {
        'access_token': user.token
    }
    response = requests.get(
        f'http://localhost:5002/users/{user.user_id}',
        cookies=cookie
    )
    return response.status_code == 200

def user_change_username(user):
    new_username = user.username + ''.join(random.choice(letters) for _ in range(3))
    cookie = {
        'access_token': user.token
    }
    
    response = requests.put(
        f'http://localhost:5002/users/{user.user_id}',
        headers={'Content-Type': 'application/json'},
        cookies=cookie,
        json={'username': new_username}
    )
    if response.status_code == 200:
        user.username = new_username
    return response.status_code == 200

def user_change_email(user):
    new_email = f"{user.username}_{random.randint(1, 9999)}@test.com"
    cookie = {
        'access_token': user.token
    }
    
    response = requests.put(
        f'http://localhost:5002/users/{user.user_id}',
        headers={'Content-Type': 'application/json'},
        cookies=cookie,
        json={'email': new_email}
    )
    if response.status_code == 200:
        user.email = new_email 
    return response.status_code == 200

def users_list(user):
    cookie = {
        'access_token': user.token
    }
    response = requests.get(
            'http://localhost:5002/users',
            cookies=cookie
        )
    return response.status_code == 200

def user_delete(user):
    cookie = {
        'access_token': user.token
    }
    response = requests.delete(
        f'http://localhost:5002/users/{user.user_id}',
        cookies=cookie
    )
    return response.status_code == 200
