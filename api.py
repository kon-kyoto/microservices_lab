from flask import Flask, jsonify
import os

app = Flask(__name__)
LOG_FILE = "/data/log.txt"

@app.route('/stats')
def stats():
    if not os.path.exists(LOG_FILE):
        return jsonify({"error": "No log file"}), 404
    
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()

    return jsonify({
        "total_entries": len(lines),
        "last_entry": lines[-1].strip() if lines else None
    })

@app.route('/health')
def health():
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
