import os
import shutil

source_dir = r'C:\Users\namul\Desktop\2026_MDP\archive\marvel\0017'
target_dir = r'C:\Users\namul\Desktop\2026_MDP\dataset\train\images'
prefix = "marvel_0017_"
def move_and_rename_images(src, dst, file_prefix):
    if not os.path.exists(dst):
        os.makedirs(dst)
        print(f"생성한 폴더: {dst}")

    files = os.listdir(src)
    count = 0

    for filename in files:
        old_path = os.path.join(src, filename)
        
        if os.path.isfile(old_path):
            new_filename = file_prefix + filename
            new_path = os.path.join(dst, new_filename)

            shutil.copy2(old_path, new_path)
            count += 1
            print(f"이동 완료: {filename} -> {new_filename}")

    print(f"이동한 총 파일 개수: {count}")

if __name__ == "__main__":
    move_and_rename_images(source_dir, target_dir, prefix)