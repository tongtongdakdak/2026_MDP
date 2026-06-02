import os
import pandas as pd
import shutil
from sklearn.model_selection import train_test_split

base_dir = r"C:\Users\namul\Desktop\2026_MDP"
source_img_dir = os.path.join(base_dir, "captured_frames", "captured_frames")
source_csv_path = os.path.join(base_dir, "captured_frames", "annotations.csv")

target_base = os.path.join(base_dir, "dataset")
all_images = [f for f in os.listdir(source_img_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
df_ann = pd.read_csv(source_csv_path)

# 7:1.5:1.5
train_imgs, temp_imgs = train_test_split(all_images, test_size=0.3, random_state=6974)
val_imgs, test_imgs = train_test_split(temp_imgs, test_size=0.5, random_state=6974)

splits = {
    "train": train_imgs,
    "val": val_imgs,
    "test": test_imgs
}

def process_split(split_name, image_list):
    target_dir = os.path.join(target_base, split_name)
    img_target_dir = os.path.join(target_dir, "images")
    
    if not os.path.exists(img_target_dir):
        os.makedirs(img_target_dir)
    
    target_csv_path = os.path.join(target_dir, f"{split_name}.csv")
    
    split_df = df_ann[df_ann['dir'].isin(image_list)]
    
    for img_name in image_list:
        src_path = os.path.join(source_img_dir, img_name)
        dst_path = os.path.join(img_target_dir, img_name)
        if os.path.exists(src_path):
            shutil.move(src_path, dst_path)

    if os.path.exists(target_csv_path):
        with open(target_csv_path, 'a+') as f:
            f.seek(0, os.SEEK_END)
            if f.tell() > 0:
                f.seek(f.tell() - 1)
                last_char = f.read(1)
                if last_char != '\n':
                    f.write('\n')
        split_df.to_csv(target_csv_path, mode='a', index=False, header=False)
    else:
        split_df.to_csv(target_csv_path, index=False)
    final_df = pd.read_csv(target_csv_path, on_bad_lines='skip')
    final_df = final_df[final_df['dir'] != 'dir'] 
    final_df.to_csv(target_csv_path, index=False)
    
    print(f"[{split_name}] 처리,이미지 {len(image_list)}개 이동)")

for split_name, image_list in splits.items():
    process_split(split_name, image_list)
if os.path.exists(source_csv_path):
    empty_df = pd.DataFrame(columns=df_ann.columns)
    empty_df.to_csv(source_csv_path, index=False)
    print(f"CSV({source_csv_path})가 초기호ㅏ")

print("\ntask가 성공적으로 끝났따는 것이야!")