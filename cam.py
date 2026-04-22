import cv2
from ultralytics import YOLO
from picamera2 import Picamera2

model = YOLO('best.pt')

picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (320, 240)}
)
picam2.configure(config)
picam2.start()

while True:
    frame = picam2.capture_array()
    
    if frame is None:
        print("frame None")
        break

    if frame.shape[2] == 4:
        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)

 
    results = model.predict(frame, stream=True)

    for result in results:
        count = len(result.boxes)
        annotated_frame = result.plot()

        cv2.putText(annotated_frame, f"num: {count}", (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("YOLO", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

picam2.stop()
cv2.destroyAllWindows()
