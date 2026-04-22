import os

root_dir = r'dataset'

def update_class_id_to_zero(directory):
    count = 0
    
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.lower().endswith('.txt'):
                file_path = os.path.join(root, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    if not lines:
                        continue
                        
                    new_lines = []
                    for line in lines:
                        parts = line.split()
                        if len(parts) > 0:
                            parts[0] = '0'
                            new_lines.append(" ".join(parts) + "\n")
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)
                    
                    count += 1

                except Exception as e:
                    print(f"오류 발생 ({filename}): {e}")

    print("-----------------")
    print(f"{count}개의 텍스트 파일 내 클래스 ID를 0으로 변경")

# 함수 실행
if __name__ == "__main__":
    update_class_id_to_zero(root_dir)