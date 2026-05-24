from flask import Flask, request, jsonify
import hashlib
import uuid

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

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
