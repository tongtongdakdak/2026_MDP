from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import threading
import serial
import time

app = Flask(__name__)
CORS(app)

latest_data = {f"Room_{i}": {"figure_count": 0, "fire_detected": False} for i in range(1, 16)}
for i in range(1, 8):
    latest_data[f"Hallway_{i}"] = {"figure_count": 0, "fire_detected": False}

latest_routes = {}

SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200

def serial_reader_thread():
    while True:
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            while True:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if ":" in line:
                        zone_name, fire_status = line.split(":")
                        if zone_name in latest_data:
                            latest_data[zone_name]['fire_detected'] = (fire_status == "1")
                        
                        fire_zones = [zone for zone, data in latest_data.items() if data['fire_detected']]
                        if fire_zones:
                            msg = f"FIRE:{','.join(fire_zones)}\n"
                            ser.write(msg.encode('ascii'))
                        else:
                            ser.write(b"SAFE\n")
        except:
            time.sleep(3)

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
    serial_thread = threading.Thread(target=serial_reader_thread, daemon=True)
    serial_thread.start()
    app.run(host='0.0.0.0', port=5000)