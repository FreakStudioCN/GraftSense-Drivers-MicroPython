# Python env   : Python v3.12.0
# -*- coding: utf-8 -*-
# @Time    : 2026/2/12 下午6:36
# @Author  : 李清水
# @File    : modify_package_json.py
# @Description : 批量修改package.json文件，支持urls路径转换、字段标准化及备份清理

import os
import json
import shutil

def backup_file(file_path):
    """备份文件，生成 .bak 后缀的备份文件"""
    backup_path = f"{file_path}.bak"
    try:
        shutil.copy2(file_path, backup_path)
        return True, f"已备份至 {backup_path}"
    except Exception as e:
        return False, f"备份失败: {str(e)}"

def extract_parent_dir_from_url(url):
    """从原urls的路径中提取.py文件的上一级目录名"""
    # 分割路径
    parts = url.split('/')
    # 找到最后一个.py文件的位置
    for i, part in reversed(list(enumerate(parts))):
        if part.endswith('.py'):
            # 返回上一级目录名
            if i > 0:
                return parts[i - 1]
            else:
                return ''  # 如果.py文件在根目录，返回空
    return ''

def delete_bak_files(project_root):
    """遍历项目目录，删除所有package.json.bak文件"""
    print("\n" + "=" * 80)
    print("开始清理备份文件（.bak）")
    print("=" * 80)

    delete_success = 0
    delete_fail = 0
    fail_files = []

    # 遍历项目根目录下的所有子目录
    for entry in os.scandir(project_root):
        if entry.is_dir() and not entry.name.startswith('.'):
            subdir_path = entry.path

            # 遍历驱动文件夹（以_driver结尾）
            for driver_folder in os.listdir(subdir_path):
                driver_path = os.path.join(subdir_path, driver_folder)
                if not os.path.isdir(driver_path) or not driver_folder.endswith("_driver"):
                    continue

                bak_file_path = os.path.join(driver_path, "package.json.bak")
                if os.path.exists(bak_file_path):
                    try:
                        os.remove(bak_file_path)
                        delete_success += 1
                        print(f"✅ 已删除备份文件: {bak_file_path}")
                    except Exception as e:
                        delete_fail += 1
                        fail_files.append(f"{bak_file_path} - {str(e)}")
                        print(f"❌ 删除失败: {bak_file_path} - {str(e)}")

    # 输出删除统计
    print("\n备份文件清理完成！统计：")
    print(f"成功删除：{delete_success} 个")
    print(f"删除失败：{delete_fail} 个")
    if fail_files:
        print("\n删除失败的文件：")
        for f in fail_files:
            print(f"  - {f}")
    print("=" * 80)


def modify_single_package_json(package_json_path):
    """修改单个package.json文件，从原urls路径提取目录名"""
    # 1. 备份原文件
    backup_success, backup_msg = backup_file(package_json_path)
    if not backup_success:
        return False, f"【备份失败】{package_json_path} - {backup_msg}"

    # 2. 读取并解析原文件
    try:
        with open(package_json_path, "r", encoding="utf-8") as f:
            original_data = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"【解析失败】{package_json_path} - JSON格式错误: {str(e)}"
    except Exception as e:
        return False, f"【读取失败】{package_json_path} - {str(e)}"

    # 3. 构建新的JSON结构
    new_data = {}

    # 保留核心字段
    new_data["name"] = original_data.get("name", os.path.basename(os.path.dirname(package_json_path)))
    new_data["version"] = original_data.get("version", "1.0.0")
    new_data["description"] = original_data.get("description",
                                                f"A MicroPython library to control {new_data['name'].replace('_driver', '')} driver")
    new_data["author"] = original_data.get("author", "unknown")

    # 新增固定字段
    new_data["license"] = "MIT"
    new_data["chips"] = "all"
    new_data["fw"] = "all"
    new_data["_comments"] = {
        "chips": "该包支持运行的芯片型号，all表示无芯片限制",
        "fw": "该包依赖的特定固件如ulab、lvgl,all表示无固件依赖"
    }

    # 4. 处理urls字段（从原路径提取目录名）
    original_urls = original_data.get("urls", [])
    new_urls = []
    errors = []

    if original_urls:
        for idx, url_entry in enumerate(original_urls):
            if len(url_entry) == 2:
                source_file, target_path = url_entry
                # 从原路径中提取.py文件的上一级目录名
                parent_dir = extract_parent_dir_from_url(target_path)
                if parent_dir:
                    new_target = f"{parent_dir}/{source_file}"
                else:
                    new_target = source_file  # 如果在根目录，直接用文件名
                new_urls.append([source_file, new_target])
            else:
                errors.append(f"条目{idx + 1}格式不正确: {url_entry}")
    else:
        # 无urls时，尝试从驱动名推断（兜底）
        driver_name = new_data["name"].replace("_driver", "")
        default_file = f"{driver_name}.py"
        new_urls = [[default_file, default_file]]

    new_data["urls"] = new_urls

    # 5. 写入修改后的内容
    try:
        with open(package_json_path, "w", encoding="utf-8") as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        # 生成修改日志
        modify_log = (
            f"【修改成功】{package_json_path}\n"
            f"  - 保留字段：name={new_data['name']}, version={new_data['version']}\n"
            f"  - 新增字段：license=MIT, chips=all, fw=all, _comments\n"
            f"  - urls修改：{original_urls} → {new_urls}\n"
            f"  - {backup_msg}"
        )
        if errors:
            modify_log += f"\n  - 警告：以下条目格式错误，已跳过：{', '.join(errors)}"
        return True, modify_log
    except Exception as e:
        return False, f"【写入失败】{package_json_path} - {str(e)}"


def batch_modify_package_json(project_root):
    """批量修改所有驱动文件夹下的package.json"""
    print("=" * 80)
    print("开始批量修改package.json文件（从原urls路径提取目录名）")
    print(f"项目根目录：{project_root}")
    print("=" * 80)

    success_count = 0
    fail_count = 0
    total_count = 0
    fail_list = []

    # 遍历项目根目录下的所有子目录
    for entry in os.scandir(project_root):
        if entry.is_dir() and not entry.name.startswith('.'):
            subdir_path = entry.path

            # 遍历驱动文件夹（以_driver结尾）
            for driver_folder in os.listdir(subdir_path):
                driver_path = os.path.join(subdir_path, driver_folder)
                if not os.path.isdir(driver_path) or not driver_folder.endswith("_driver"):
                    continue

                package_json_path = os.path.join(driver_path, "package.json")
                if not os.path.exists(package_json_path):
                    print(f"⚠️  跳过：{driver_folder} 无package.json文件")
                    continue

                total_count += 1
                print(f"\n[{total_count}] 处理：{package_json_path}")

                # 修改单个文件
                success, msg = modify_single_package_json(package_json_path)
                if success:
                    success_count += 1
                    print(f"✅ {msg}")
                else:
                    fail_count += 1
                    fail_list.append(msg)
                    print(f"❌ {msg}")

    # 输出最终统计
    print("\n" + "=" * 80)
    print("批量修改完成！统计结果：")
    print(f"总处理文件数：{total_count}")
    print(f"修改成功：{success_count}")
    print(f"修改失败：{fail_count}")

    if fail_list:
        print("\n失败列表：")
        for fail_msg in fail_list:
            print(f"  - {fail_msg}")
    print("=" * 80)

    # 调用删除bak文件的函数
    delete_bak_files(project_root)

if __name__ == "__main__":
    # 获取脚本所在目录作为项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    # 执行批量修改
    batch_modify_package_json(project_root)