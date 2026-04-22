import cv2
from ultralytics import YOLO

class ObjectDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.cap = None

    def run(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index)
        
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break

            results = self.model.predict(frame, stream=True)

            for result in results:
                annotated_frame = result.plot()
                
                classes = result.boxes.cls.tolist()
                # person_count = classes.count(1)
                lego_count = classes.count(0)

                # cv2.putText(annotated_frame, f"Person: {person_count}", (20, 50), 
                #             cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                cv2.putText(annotated_frame, f"Lego: {lego_count}", (20, 100), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

                cv2.imshow("detection", annotated_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.stop()

    def stop(self):
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    detector = ObjectDetector(model_path='best.pt')
    detector.run()