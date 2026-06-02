import cv2
import requests
import time
from ultralytics import YOLO
from shapely.geometry import Point, Polygon

class ObjectDetector:
    def __init__(self, model_path='best.pt', server_url='http://127.0.0.1:5000/detection'):
        self.model = YOLO(model_path)
        self.server_url = server_url
        self.cap = None
        self.last_sent_time = 0
        
        self.zones = {
            "방_1": Polygon([(0, 0), (110, 0), (110, 150), (0, 150)]),
            "방_2": Polygon([(110, 0), (190, 0), (190, 150), (110, 150)]),
            "방_3": Polygon([(190, 0), (320, 0), (320, 190), (190, 190)]),
            "방_4": Polygon([(320, 0), (415, 0), (415, 190), (320, 190)]),
            "방_5": Polygon([(415, 0), (510, 0), (510, 190), (415, 190)]),
            "방_6": Polygon([(510, 0), (660, 0), (660, 190), (510, 190)]),
            "방_7": Polygon([(0, 250), (190, 250), (190, 440), (0, 440)]),
            "방_8": Polygon([(190, 250), (290, 250), (290, 345), (190, 345)]),
            "방_9": Polygon([(190, 345), (290, 345), (290, 440), (190, 440)]),
            "방_10": Polygon([(340, 250), (440, 250), (440, 440), (340, 440)]),
            "방_11": Polygon([(440, 250), (530, 250), (530, 310), (440, 310)]),
            "방_12": Polygon([(440, 310), (530, 310), (530, 370), (440, 370)]),
            "방_13": Polygon([(440, 370), (530, 370), (530, 440), (440, 440)]),
            "방_14": Polygon([(530, 370), (660, 370), (660, 440), (530, 440)]),
            "방_15": Polygon([(570, 190), (660, 190), (660, 340), (570, 340)]),
            
            "복도_1": Polygon([(0, 150), (190, 150), (190, 250), (0, 250)]),
            "복도_2": Polygon([(190, 190), (290, 190), (290, 250), (190, 250)]),
            "복도_3": Polygon([(290, 190), (440, 190), (440, 250), (290, 250)]),
            "복도_4": Polygon([(440, 190), (570, 190), (570, 150), (660, 150), (660, 190), (440, 190)]),
            "복도_5": Polygon([(290, 250), (340, 250), (340, 440), (290, 440)]),
            "복도_6": Polygon([(440, 250), (530, 250), (530, 440), (440, 440)]),
            "복도_7": Polygon([(570, 190), (660, 190), (660, 370), (530, 370), (530, 440), (660, 440), (660, 190)])
        }

    def send_to_server(self, data):
        try:
            requests.post(self.server_url, json=data, timeout=0.3)
        except requests.exceptions.RequestException:
            pass

    def run(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            return
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break
            results = self.model.predict(frame, stream=True, verbose=False)
            zone_status = {zone_name: {"figure_count": 0, "fire_detected": False} for zone_name in self.zones.keys()}
            for result in results:
                annotated_frame = result.plot()
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    if conf < 0.25:
                        continue
                    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                    object_point = Point(cx, cy)
                    for zone_name, zone_polygon in self.zones.items():
                        if zone_polygon.contains(object_point):
                            if cls == 0:
                                zone_status[zone_name]["figure_count"] += 1
                            elif cls == 1:
                                zone_status[zone_name]["fire_detected"] = True
                                break
                current_time = time.time()
                if current_time - self.last_sent_time >= 0.5:
                    self.send_to_server(zone_status)
                    self.last_sent_time = current_time
                cv2.imshow("Detection", annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        self.stop()

    def stop(self):
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    detector = ObjectDetector()
    detector.run()