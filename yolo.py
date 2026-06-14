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
            "Room_1": Polygon([(0, 0), (110, 0), (110, 150), (0, 150)]),
            "Room_2": Polygon([(110, 0), (190, 0), (190, 150), (110, 150)]),
            "Room_3": Polygon([(190, 0), (320, 0), (320, 190), (190, 190)]),
            "Room_4": Polygon([(320, 0), (415, 0), (415, 190), (320, 190)]),
            "Room_5": Polygon([(415, 0), (510, 0), (510, 190), (415, 190)]),
            "Room_6": Polygon([(510, 0), (660, 0), (660, 190), (510, 190)]),
            "Room_7": Polygon([(0, 250), (190, 250), (190, 440), (0, 440)]),
            "Room_8": Polygon([(190, 250), (290, 250), (290, 440), (190, 440)]),
            "Room_9": Polygon([(290, 350), (390, 350), (390, 440), (290, 440)]),
            "Room_10": Polygon([(330, 250), (390, 250), (390, 350), (330, 350)]),
            "Room_11": Polygon([(440, 250), (530, 250), (530, 310), (440, 310)]),
            "Room_12": Polygon([(440, 310), (530, 310), (530, 370), (440, 370)]),
            "Room_13": Polygon([(440, 370), (530, 370), (530, 440), (440, 440)]),
            "Room_14": Polygon([(530, 370), (660, 370), (660, 440), (530, 440)]),
            "Room_15": Polygon([(580, 250), (660, 250), (660, 370), (580, 370)]),
            "Hallway_1": Polygon([(0, 150), (190, 150), (190, 250), (0, 250)]),
            "Hallway_2": Polygon([(190, 190), (320, 190), (320, 250), (190, 250)]),
            "Hallway_3": Polygon([(320, 190), (415, 190), (415, 250), (320, 250)]),
            "Hallway_4": Polygon([(415, 190), (660, 190), (660, 250), (415, 250)]),
            "Hallway_5": Polygon([(290, 250), (330, 250), (330, 350), (290, 350)]),
            "Hallway_6": Polygon([(530, 250), (580, 250), (580, 370), (530, 370)]),
            "Hallway_7": Polygon([(390, 250), (440, 250), (440, 440), (390, 440)])
        }

    def send_to_server(self, data):
        try:
            requests.post(self.server_url, json=data, timeout=0.5)
        except:
            pass

    def run(self, source=0):
        self.cap = cv2.VideoCapture(source)
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break
            results = self.model(frame, verbose=False)
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