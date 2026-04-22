import os
from ultralytics import YOLO


DRIVE_SAVE_PATH = r'C:\Users\namul\Desktop\2026_MDP'
DATA_YAML_PATH = r'dataset\data.yaml'

def train_yolo():
    last_checkpoint = os.path.join(DRIVE_SAVE_PATH, 'figure_detection/weights/last.pt')

    if os.path.exists(last_checkpoint):
        #이전학습 진행
        model = YOLO(last_checkpoint)
        resume_flag = True
    else:
        #새로 학습
        model = YOLO('yolo26n.pt')
        resume_flag = False

    model.train(
        data=DATA_YAML_PATH,
        epochs=100,
        imgsz=640,
        batch=16,
        project=DRIVE_SAVE_PATH,
        name='figure_detection',
        resume=resume_flag,

        save=True,
        save_period=1,
        exist_ok=True,

        patience=30,
        optimizer='AdamW',
        cos_lr=True,
        close_mosaic=10,
        device="cpu" #GPU쓸거임ㅇㅇ
    )