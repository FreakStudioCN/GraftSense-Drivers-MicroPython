import os

# 1. 配置核心参数（固定根目录，无需修改，直接使用）
root_dir = r"D:\GraftSense-Drivers-MicroPython"
# 存储最终识别到的下两级文件夹完整路径（名称）
two_level_folders = []
prefix_cmd = "mpremote mip install github:FreakStudioCN/GraftSense-Drivers-MicroPython/"
# 2. 第一步：遍历根目录下的【一级子文件夹】（如下的communication）
for first_level_folder in os.listdir(root_dir):
    first_level_path = os.path.join(root_dir, first_level_folder)
    # 仅筛选根目录下的一级文件夹（排除文件）
    if not os.path.isdir(first_level_path):
        continue
    
    # 3. 第二步：遍历一级文件夹下的【二级子文件夹】（如下的cc2530_driver、hc08_driver）
    for second_level_folder in os.listdir(first_level_path):
        second_level_path = os.path.join(first_level_path, second_level_folder)
        # 仅筛选一级文件夹下的二级文件夹（排除文件，确保是下两级文件夹）
        if os.path.isdir(second_level_path):
            # 可选1：存储【完整本地路径】（如 D:\GraftSense-Drivers-MicroPython\communication\cc2530_driver）
            # two_level_folders.append(second_level_path)
            
            # 可选2：存储【相对层级名称】（如 communication\cc2530_driver，更贴合你的需求）
            relative_two_level = os.path.join(first_level_folder, second_level_folder)
            two_level_folders.append(relative_two_level)
            print(f"已识别下两级文件夹：{relative_two_level}")

# 4. 将所有下两级文件夹名称写入txt文件（生成在根目录下）
txt_save_path = os.path.join(root_dir, "two_level_folders.txt")
with open(txt_save_path, "w", encoding="utf-8") as f:
    for folder in two_level_folders:
        folder_normalized = folder.replace("\\", "/")
        full_cmd = f"{prefix_cmd}{folder_normalized}"
        f.write(full_cmd + "\n")

# 5. 打印执行结果，确认状态
if two_level_folders:
    print(f"\n执行成功！共识别 {len(two_level_folders)} 个下两级文件夹")
    print(f"文件夹名称已写入：{txt_save_path}")
else:
    print(f"\n未在根目录 {root_dir} 下识别到任何下两级文件夹！")