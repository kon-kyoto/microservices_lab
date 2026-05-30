
import requests
import random
import strins:

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
