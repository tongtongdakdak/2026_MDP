import os
from ultralytics import YOLO

DRIVE_SAVE_PATH = r'C:\Users\namul\Desktop\2026_MDP'
DATASET_ROOT = os.path.join(DRIVE_SAVE_PATH, 'dataset')
NEW_DATA_ROOT = os.path.join(DATASET_ROOT, 'new_data.yaml')
DATA_YAML_PATH = os.path.join(DATASET_ROOT, 'data.yaml')

def train_yolo():
    last_checkpoint = os.path.join(DRIVE_SAVE_PATH, 'lego_detection_5/weights/last.pt')

    if os.path.exists(last_checkpoint):
        model = YOLO(last_checkpoint)
        model.train(resume=True)
    else:
        model = YOLO('yolo26n.pt') 
        
        model.train(
            data=r"C:\Users\namul\Desktop\2026_MDP\dataset\data.yaml",
            epochs=500,
            patience=50,
            batch=16,
            imgsz=640,
            device='cpu',
            optimizer='AdamW',
            lr0=1e-6,
            cos_lr=False,
            close_mosaic=25,
            cls=5.5,
            box=9.5,
            dfl=2.0,
            degrees=25.0,
            flipud=0.5,
            fliplr=0.5,
            project=r"C:\Users\namul\Desktop\2026_MDP",
            name="lego_detection_5",
            exist_ok=True
        )