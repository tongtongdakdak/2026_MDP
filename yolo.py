import cv2
import os
import json
import requests
import time
from ultralytics import YOLO
from shapely.geometry import Point, Polygon
from picamera2 import Picamera2

class ObjectDetector:
    def __init__(self, model_path='best.pt', server_url='http://127.0.0.1:5000/detection'):
        self.model = YOLO(model_path)
        self.server_url = server_url
        self.picam = None
        self.last_sent_time = 0

        self.zones = {}
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zones_config.json')
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    zones_data = json.load(f)
                
                for zone_name, pts in zones_data.items():
                    self.zones[zone_name] = Polygon(pts)
                print(f"[INFO] {len(self.zones)}zone data successfully loaded.")
            except Exception as e:
                print(f"error: zones_config.json load failed: {e}")
        else:
            print(f"error: sector setting file found error: {config_path}")
        
    def send_to_server(self, data):
        try:
            requests.post(self.server_url, json=data, timeout=0.3)
        except requests.exceptions.RequestException:
            pass

    def run(self):
        self.picam = Picamera2()
        config = self.picam.create_preview_configuration(
            main={"format": "BGR888", "size": (660, 440)}
        )
        self.picam.configure(config)
        self.picam.start()
        print("[INFO] camera started")
        time.sleep(1)

        while True:
            frame = self.picam.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            frame = cv2.rotate(frame, cv2.ROTATE_180)
            
            results = self.model.predict(frame, stream=False, verbose=False, conf = 0.4)
            
            zone_status = {zone_name: {"figure_count": 0, "fire_detected": False}
                           for zone_name in self.zones.keys()}
                           
            annotated_frame = frame.copy()

            for result in results:
                annotated_frame = result.plot()
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    if cls == 0 and conf < 0.4:
                        continue
                    if cls == 1 and conf < 0.4: 
                        continue
                        
                    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                    object_point = Point(cx, cy)
                    
                    for zone_name, zone_polygon in self.zones.items():
                        if zone_polygon.contains(object_point):
                            if cls == 0:
                                zone_status[zone_name]["figure_count"] += 1
                            elif cls == 1:
                                zone_status[zone_name]["fire_detected"] = True

            current_time = time.time()
            if current_time - self.last_sent_time >= 0.5:
                self.send_to_server(zone_status)
                self.last_sent_time = current_time

            if annotated_frame is not None:
                cv2.imshow("YOLO Detection", annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.stop()

    def stop(self):
        if self.picam:
            self.picam.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    detector = ObjectDetector()
    detector.run()