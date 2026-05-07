import cv2
import torch
import pandas as pd

class FireDetect:
    def __init__(self, model_path):
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path)
        self.cap = None

    def process_frame(self, frame):
        results = self.model(frame)
        
        annotated_frame = results.render()[0].copy()
        
        count = len(results.pandas().xyxy[0])
        is_fire = count >= 1
        
        return annotated_frame, is_fire

    def run(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index)
        
        if not self.cap.isOpened():
            print("카메라를 열 수 없습니다.")
            return
        
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break

            display_frame, fire_detected = self.process_frame(frame)

            label = "fire O" if fire_detected else "fire X"
            color = (0, 0, 255) if fire_detected else (0, 255, 0)
            
            cv2.putText(display_frame, label, (20, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

            cv2.imshow("fire_detection", display_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.stop()

    def stop(self):
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("햣!종료")

if __name__ == "__main__":
    detector = FireDetect(model_path='yolov5s_fire.pt')
    detector.run()