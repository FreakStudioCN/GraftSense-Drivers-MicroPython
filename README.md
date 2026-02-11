import os

def rename_all_files_to_readme(folder_path):
    """
    将指定文件夹下的所有文件重命名为README.md（多文件自动加数字后缀）
    :param folder_path: 目标文件夹路径
    """
    # 1. 检查文件夹是否存在
    if not os.path.isdir(folder_path):
        print(f"错误：文件夹 {folder_path} 不存在！")
        return
    
    # 2. 遍历文件夹，筛选出所有文件（排除子文件夹）
    all_files = []
    for file_name in os.listdir(folder_path):
        file_full_path = os.path.join(folder_path, file_name)
        # 只处理文件，跳过文件夹
        if os.path.isfile(file_full_path):
            all_files.append(file_full_path)
    
    # 3. 无文件时提示
    if not all_files:
        print(f"文件夹 {folder_path} 下未找到任何文件！")
        return
    
    # 4. 批量重命名（核心逻辑）
    success_count = 0
    for idx, old_file_path in enumerate(all_files):
        # 构造新文件名：第一个文件为README.md，后续为README_1.md、README_2.md...
        if idx == 0:
            new_file_name = "README.md"
        else:
            new_file_name = f"README_{idx}.md"
        
        # 拼接新文件的完整路径
        new_file_path = os.path.join(folder_path, new_file_name)
        
        # 执行重命名，捕获异常（如权限不足、文件被占用）
        try:
            os.rename(old_file_path, new_file_path)
            print(f"✅ 成功：{old_file_path} → {new_file_path}")
            success_count += 1
        except Exception as e:
            print(f"❌ 失败：{old_file_path} → 原因：{str(e)}")
    
    # 5. 输出最终结果
    print(f"\n📊 处理完成！共找到 {len(all_files)} 个文件，成功重命名 {success_count} 个。")

# ===================== 核心配置（必改） =====================
# 请替换为你的目标文件夹路径
# Windows示例：target_folder = "C:\\Users\\你的用户名\\Desktop\\测试文件夹"
# Linux/macOS示例：target_folder = "/Users/你的用户名/Desktop/测试文件夹"
target_folder = "D:\GraftSense-Drivers-MicroPython"
# ============================================================

# 执行重命名
if __name__ == "__main__":
    rename_all_files_to_readme(target_folder)