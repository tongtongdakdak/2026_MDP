import cv2
from fire import FireDetect
from person_lego import ObjectDetector

def main():
    fire_detector = FireDetect(model_path='yolov5s_fire.pt')
    object_detector = ObjectDetector(model_path='best.pt')

    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        _, fire_detected = fire_detector.process_frame(frame)
        
        results = object_detector.model.predict(frame, stream=True)
        
        for result in results:
            combined_frame = result.plot()
            
            classes = result.boxes.cls.tolist()
            # p_count = classes.count(1)
            l_count = classes.count(0)

            fire_label = "Fire: O" if fire_detected else "Fire: X"
            fire_color = (0, 0, 255) if fire_detected else (0, 255, 0)
            cv2.putText(combined_frame, fire_label, (20, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, fire_color, 2)

            # cv2.putText(combined_frame, f"Person: {p_count}", (20, 100), 
            #             cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            cv2.putText(combined_frame, f"Lego: {l_count}", (20, 150), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

            cv2.imshow("Integrated Detection", combined_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()