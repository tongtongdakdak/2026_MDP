import os
import json
from ultralytics import YOLO
from peft import LoraConfig, get_peft_model

DRIVE_SAVE_PATH = r'C:\Users\namul\Desktop\2026_MDP'

def train_yolo():
    model = YOLO('yolo26n.pt') 

    base_model = model.model
    for param in base_model.parameters():
        param.requires_grad = False

    peft_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["cv1", "cv2"],
        lora_dropout=0.05,
        bias="none"
    )

    model.model = get_peft_model(base_model, peft_config)
    
    model.model.print_trainable_parameters()

    config_path = os.path.join(DRIVE_SAVE_PATH, 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        train_config = json.load(f)

    model.train(**train_config)