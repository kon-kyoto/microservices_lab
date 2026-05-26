from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/user/<id>', methods=['GET'])
def get_user(id):
    return jsonify({"message": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5001')
