import cv2
import time
import os

def capture_frames_for_5_seconds():
    folder_name = "captured_frames"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    picam2 = Picamera2()
    config = picam2.create_preview_configuration(
    main={"size": (320, 240)}
    )
    picam2.configure(config)
    picam2.start()

    if not cap.isOpened():
        print("카메라를 열기 불가능.")
        return

    print("5초간 촬영")
    
    start_time = time.time()
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("프레임.")
            break

        file_path = os.path.join(folder_name, f"frame_{frame_count:04d}.jpg")
        cv2.imwrite(file_path, frame)
        
        cv2.imshow('cam', frame)

        frame_count += 1
        
        if time.time() - start_time > 5:
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    print(f"프레임 수:{frame_count}, 저장된 폴더: {folder_name}")
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    capture_frames_for_5_seconds()