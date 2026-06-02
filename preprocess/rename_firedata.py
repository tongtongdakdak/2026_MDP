import os

# 작업할 디렉토리 경로
target_dir = r"C:\Users\namul\Desktop\Fire.v1i.yolo26"

# 디렉토리 내 모든 파일 확인
files = os.listdir(target_dir)
txt_files = [f for f in files if f.endswith('.txt')]

converted_count = 0

for file_name in txt_files:
    file_path = os.path.join(target_dir, file_name)
    
    # 1. 파일 읽기
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            new_lines.append(line)
            continue
            
        tokens = stripped_line.split()
        if tokens and tokens[0] == '0':
            tokens[0] = '1'
            new_lines.append(" ".join(tokens) + "\n")
            modified = True
        else:
            new_lines.append(line)
            
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        converted_count += 1

print(f"수정한 파일 개수 {converted_count}")