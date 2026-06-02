import os
import pandas as pd
import cv2
DATASET_ROOT = os.path.join(r'C:\Users\namul\Desktop\2026_MDP', 'dataset')

def convert_all_csv_to_yolo():
    splits = ['train', 'val', 'test']

    for split in splits:
        split_dir = os.path.join(DATASET_ROOT, split)
        csv_path = os.path.join(split_dir, f'{split}.csv')
        img_dir = os.path.join(split_dir, 'images')
        label_dir = os.path.join(split_dir, 'labels')

        if not os.path.exists(csv_path):
            continue

        os.makedirs(label_dir, exist_ok=True)
        df = pd.read_csv(csv_path)

        for img_name, group in df.groupby('dir'):
            img_path = os.path.join(img_dir, img_name)
            img = cv2.imread(img_path)
            if img is None:
                continue
            
            h_orig, w_orig = img.shape[:2]
            txt_name = os.path.splitext(img_name)[0] + ".txt"
            txt_path = os.path.join(label_dir, txt_name)
            
            with open(txt_path, 'w') as f:
                for _, row in group.iterrows():
                    x_center = ((row['x1'] + row['x2']) / 2.0) / w_orig
                    y_center = ((row['y1'] + row['y2']) / 2.0) / h_orig
                    w = (row['x2'] - row['x1']) / w_orig
                    h = (row['y2'] - row['y1']) / h_orig
                    
                    f.write(f"0 {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}\n")
