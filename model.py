import os
import json
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
        
        config_path = os.path.join(DRIVE_SAVE_PATH, 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            train_config = json.load(f)
        
        model.train(**train_config)