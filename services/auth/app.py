from flask import Flask, request, jsonify
import jwt
import hashlib
import uuid
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'just_for_study_is_here'

users_db = {}
tokens_blacklist = set()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username in users_db:
        return jsonify({'error':'User exist'}), 400

    user_id = str(uuid.uuid4())
    users_db[username] = {
            "password_hash": hash_password(password),
            "user_id":user_id
        }

    return jsonify({'message':'User created', 'user_id': user_id}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = users_db.get(username)

    if not user:
        return jsonify({'message': 'User not exist'})


    if user['password_hash'] != hash_password(password):
        return jsonify({'message': 'Incorrect password'})

    token = jwt.encode(
            {
                'user_id': user['user_id'],
                'username': username,
                'exp': datetime.utcnow() + timedelta(hours=1)
            },
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )

    return jsonify({'access_token': token, 'token_type': "Bearer"})

@app.route('/verify', methods=['POST'])
def verify():
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.replace('Bearer ', '')

    if token in tokens_blacklist:
        return jsonify({"valid": False, "error": "Token revoked"}), 401

    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])

        return jsonify({
            "valid": True,
            "user_id": payload['user_id'],
            "username": payload['username']
        })

    except jwt.ExpiredSignatureError:
        return jsonify({"valid": False, "error":"Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"valid": False, "error":"Invalid token"}), 401
    except:
        return jsonify({"valid": False, "error":"Server error"}), 501

@app.route('/logout', methods=['POST'])
def logout():
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.replace('Bearer ', '')
    tokens_blacklist.add(token)
    return jsonify({'message': 'logout complite'})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
