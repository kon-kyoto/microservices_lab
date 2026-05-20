from flask import Flask, jsonify
import random
app = Flask(__name__)

@app.route("/rand")
def page_rand():
    return jsonify({
        'message': f'Ur random num is {random.randint(0,1000)}',
        'port': 5003
        })

if __name__ == "__main__":
    app.run(host = '0.0.0.0', port = 5003)
