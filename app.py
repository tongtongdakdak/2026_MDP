from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

latest_data = {f"방_{i}": {"figure_count": 0, "fire_detected": False} for i in range(1, 16)}
for i in range(1, 8):
    latest_data[f"복도_{i}"] = {"figure_count": 0, "fire_detected": False}

latest_routes = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detection', methods=['POST'])
def receive_detection():
    global latest_data
    data = request.get_json()
    if not data:
        return jsonify({"status": "fail"}), 400
    for zone_name, status in data.items():
        if zone_name in latest_data:
            latest_data[zone_name]['figure_count'] = status.get('figure_count', 0)
            latest_data[zone_name]['fire_detected'] = status.get('fire_detected', False)
    return jsonify({"status": "success"}), 200

@app.route('/get-data', methods=['GET'])
def get_data():
    global latest_data
    return jsonify(latest_data), 200

@app.route('/update-routes', methods=['POST'])
def update_routes():
    global latest_routes
    data = request.get_json()
    if data:
        latest_routes = data
    return jsonify({"status": "success"}), 200

@app.route('/get-routes', methods=['GET'])
def get_routes():
    global latest_routes
    return jsonify(latest_routes), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)