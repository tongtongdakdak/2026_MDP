import os
from ultralytics import YOLO

DRIVE_SAVE_PATH = r'C:\Users\namul\Desktop\2026_MDP'
DATASET_ROOT = os.path.join(DRIVE_SAVE_PATH, 'dataset')
DATA_YAML_PATH = os.path.join(DATASET_ROOT, 'data.yaml')

def train_yolo():
    last_checkpoint = os.path.join(DRIVE_SAVE_PATH, 'lego_detection/weights/last.pt')

    if os.path.exists(last_checkpoint):
        model = YOLO(last_checkpoint)
        model.train(resume=True)
    else:
        model = YOLO('yolo26n.pt') 
        
        model.train(
            data=DATA_YAML_PATH,
            epochs=1000,
            imgsz=640,
            batch=16,
            project=DRIVE_SAVE_PATH,
            name='lego_detection',
            save=True,
            save_period=10,
            exist_ok=True,
            patience=50,
            optimizer='auto',
            cos_lr=True,
            close_mosaic=10,
            device="cpu",
            box=7.5
        )