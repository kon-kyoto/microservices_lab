from flask import Flask
import requests

app = Flask(__name__)

@app.route('/')
def index():
    response_service1 = requests.get('http://service1:5001/info')
    response_service3 = requests.get('http://service3:5003/rand')
    
    answ_text = f"Service 1 says : {response_service1}\nService 3 says : {response_service3}"

    return answ_text

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
