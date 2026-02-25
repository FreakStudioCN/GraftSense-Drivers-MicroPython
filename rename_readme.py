# Python env   : Python v3.12.0
# -*- coding: utf-8 -*-
# @Time    : 2026/2/12 下午6:36
# @Author  : 李清水
# @File    : rename_readme.py
# @Description : 递归重命名项目中所有.md文件为README.md（同目录多文件自动加数字后缀）

import os


def rename_md_to_readme_recursive(root_folder):
    """
    递归遍历根文件夹及其所有子文件夹，将所有.md文件重命名为README.md（同目录多文件加数字后缀）
    :param root_folder: 根文件夹路径
    """
    # 检查根文件夹是否存在
    if not os.path.isdir(root_folder):
        print(f"错误：根文件夹 {root_folder} 不存在！")
        return

    # 统计变量
    total_md_files = 0  # 找到的.md文件总数
    success_rename = 0  # 成功重命名的数量

    # 递归遍历所有文件夹（os.walk会自动处理子文件夹）
    for dir_path, _, file_names in os.walk(root_folder):
        # 筛选当前目录下的.md文件
        md_files_in_dir = []
        for file_name in file_names:
            # 忽略大小写（如.MD、.Md也会被处理），只保留.md文件
            if file_name.lower().endswith(".md"):
                file_full_path = os.path.join(dir_path, file_name)
                md_files_in_dir.append(file_full_path)

        # 跳过无.md文件的目录
        if not md_files_in_dir:
            continue

        total_md_files += len(md_files_in_dir)

        # 对当前目录下的.md文件重命名（防覆盖）
        for idx, old_file_path in enumerate(md_files_in_dir):
            # 构造新文件名：同目录第一个为README.md，后续加数字后缀
            if idx == 0:
                new_file_name = "README.md"
            else:
                new_file_name = f"README_{idx}.md"

            # 新文件的完整路径（和原文件同目录）
            new_file_path = os.path.join(dir_path, new_file_name)

            # 执行重命名，捕获异常
            try:
                os.rename(old_file_path, new_file_path)
                print(f"✅ 成功：{old_file_path} → {new_file_path}")
                success_rename += 1
            except Exception as e:
                print(f"❌ 失败：{old_file_path} → 原因：{str(e)}")

    # 输出最终统计结果
    print(f"\n📊 处理完成！")
    print(f"- 共找到 {total_md_files} 个.md文件（含子文件夹）")
    print(f"- 成功重命名 {success_rename} 个文件")
    print(f"- 失败 {total_md_files - success_rename} 个文件")


# ===================== 核心配置（必改） =====================
# 请替换为你的根文件夹路径
# Windows示例：root_folder = "C:\\Users\\你的用户名\\Desktop\\测试文件夹"
# Linux/macOS示例：root_folder = "/Users/你的用户名/Desktop/测试文件夹"
root_folder = "./"
# ============================================================

# 执行递归重命名
if __name__ == "__main__":
    rename_md_to_readme_recursive(root_folder)
