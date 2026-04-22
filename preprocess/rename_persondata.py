import os
import glob

# 데이터셋 루트 경로 (상황에 맞게 수정하세요)
dataset_path = r'C:\Users\namul\Desktop\person_dataset' 

txt_files = glob.glob(os.path.join(dataset_path, '**', '*.txt'), recursive=True)

print(f"총 {len(txt_files)}개의 파일을 수정합니다.")

for file_path in txt_files:
    if 'README.dataset.txt' in file_path:
        continue
    
    if 'README.roboflow.txt' in file_path:
        continue
        
    with open(file_path, 'r') as f:
        lines = f.readlines()

    with open(file_path, 'w') as f:
        for line in lines:
            if line.strip():
                parts = line.split()
                parts[0] = '1'
                f.write(' '.join(parts) + '\n')

print("변경 완료!")