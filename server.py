from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import serial
import time
import json
import os
from shapely.geometry import Polygon

app = Flask(__name__)
CORS(app)

SECTOR_1_ZONES = {"Room_1", "Room_2", "Room_3", "Room_7", "Room_8", "Room_9", "Hallway_1", "Hallway_2", "Hallway_5"}
SECTOR_2_ZONES = {"Room_4", "Room_5", "Room_6", "Room_10", "Room_11", "Room_12", "Room_13", "Room_14", "Room_15", "Hallway_3", "Hallway_4", "Hallway_6", "Hallway_7"}

all_zones = set([f"Room_{i}" for i in range(1, 16)] + [f"Hallway_{i}" for i in range(1, 8)]) | SECTOR_1_ZONES | SECTOR_2_ZONES
fire_last_seen = {zone: 0.0 for zone in all_zones}
latest_data = {zone: {"figure_count": 0, "fire_detected": False} for zone in all_zones}
latest_routes = {}
latest_directions = {"forward": [], "reverse": []}

SERIAL_PORT = '/dev/ttyAMA0'
BAUD_RATE = 115200

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zones_config.json')
zones = {}

def get_zones():
    global zones
    if not zones and os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                zones_data = json.load(f)
            new_zones = {}
            for zone_name, pts in zones_data.items():
                new_zones[zone_name] = Polygon(pts)
            zones = new_zones
            print(f"Loaded {len(zones)} zones. {CONFIG_PATH}")
        except Exception as e:
            print(f"zone load fail: {e}")
    return zones

def format_zone_name(zone_name):
    try:
        if zone_name.startswith("Room_"):
            return str(int(zone_name.split("_")[1]))
        elif zone_name.startswith("Hallway_"):
            return str(100 + int(zone_name.split("_")[1]))
    except:
        pass
    return "0"

def serial_writer_thread(): # STM
    while True:
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            print(f"serial connected to {SERIAL_PORT}")
            
            while True:
                now = time.time()
                fire_zones = [z for z, info in latest_data.items() if info.get('fire_detected', False)]
                
                if fire_zones:
                    last_fire_time = now
                    formatted_zones = [format_zone_name(z) for z in fire_zones]
                    last_fire_zone_str = formatted_zones[0] if formatted_zones else "0"

                if (now - last_fire_time) < 4.0:
                    fire_status_str = "1"
                    fire_zones_str = last_fire_zone_str
                else:
                    fire_status_str = "0"
                    fire_zones_str = "0"
                
                sector_1_count = sum(latest_data[z].get('figure_count', 0) for z in SECTOR_1_ZONES if z in latest_data)
                sector_2_count = sum(latest_data[z].get('figure_count', 0) for z in SECTOR_2_ZONES if z in latest_data)
                
                if sector_1_count > sector_2_count:
                    crowded_sector = "1"
                elif sector_2_count > sector_1_count:
                    crowded_sector = "2"
                else:
                    crowded_sector = "0"
                
                # Hallway(0: forward, 1: reverse, -1: fire, 2: confuse)
                forward_list = latest_directions.get("forward", [])
                reverse_list = latest_directions.get("reverse", [])
                
                hallway_states = []
                for i in range(1, 8):
                    h_key = f"Hallway_{i}"
                    h_name = f"Hallway{i}"
                    
                    if latest_data.get(h_key, {}).get('fire_detected', False):
                        hallway_states.append("-1")
                    elif h_name in forward_list:
                        hallway_states.append("0")
                    elif h_name in reverse_list:
                        hallway_states.append("1")
                    elif latest_data.get(h_key, {}).get('figure_count', 0) >= 3:
                        hallway_states.append("2")
                    else:
                        hallway_states.append("0")
                
                hallway_str = ",".join(hallway_states)
                
                # msg = f"{fire_status_str},{fire_zones_str},{crowded_sector},{hallway_str}\n\r"
                msg = f"{fire_status_str},{fire_zones_str},{crowded_sector}\n\r"
                                
                ser.write(msg.encode('utf-8'))
                print(f"stm send {msg.strip()}")
                time.sleep(3.0)
                
        except Exception as e:
            print(f"serial Error | disconnected. retry 3sec ({e})")
            time.sleep(3.0)

@app.route('/detection', methods=['POST']) # YOLO
def receive_detection():
    global latest_data, fire_last_seen
    payload = request.get_json()
    now = time.time()
    
    if not payload:
        return jsonify({"status": "fail"}), 400
        
    for zone_name, status in payload.items():
        if zone_name in latest_data:
            latest_data[zone_name]['figure_count'] = status.get('figure_count', 0)
            
            is_fire = status.get('fire_detected', False)
            if is_fire:
                fire_last_seen[zone_name] = now
                latest_data[zone_name]['fire_detected'] = True
            else:
                if (now - fire_last_seen[zone_name]) < 3.0:
                    latest_data[zone_name]['fire_detected'] = True
                else:
                    latest_data[zone_name]['fire_detected'] = False
                    
    return jsonify({"status": "success"}), 200

@app.route('/get-data', methods=['GET']) # evacuate
def get_data():
    global latest_data
    return jsonify(latest_data), 200

@app.route('/update-routes', methods=['POST']) # evacuate
def update_routes():
    global latest_routes, latest_directions
    data = request.get_json()
    if data:
        latest_routes = data.get("routes", {})
        latest_directions = data.get("directions", {"forward": [], "reverse": []})
    return jsonify({"status": "success"}), 200

@app.route('/get-routes', methods=['GET']) # TEST
def get_routes():
    global latest_routes
    return jsonify(latest_routes), 200

@app.route('/app-data', methods=['GET']) # android App
def get_app_data():
    global latest_data, latest_routes
    
    fire_zones = [z for z, info in latest_data.items() if info.get('fire_detected', False)]
    
    people_counts = {z: info.get('figure_count', 0) for z, info in latest_data.items()}
    
    routes = latest_routes
            
    return jsonify({
        "fire_zones": fire_zones,
        "people_counts": people_counts,
        "routes": routes
    }), 200

if __name__ == '__main__':
    serial_thread = threading.Thread(target=serial_writer_thread, daemon=True)
    serial_thread.start()
    app.run(host='0.0.0.0', port=5000)