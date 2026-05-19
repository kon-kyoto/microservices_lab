from flask import Flask
import requests

app = Flask(__name__)

@app.route('/')
def index():
    response = requests.get('http://service1:5001/info')
    return f"Service 2 says: {response.json()}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
