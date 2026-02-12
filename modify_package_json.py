# Python env   : Python v3.12.0
# -*- coding: utf-8 -*-
# @Time    : 2026/2/12 下午6:36
# @Author  : 李清水
# @File    : modify_package_json.py
# @Description : 批量修改package.json文件（支持任意深度目录、无_driver后缀限制、增强JSON容错）

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


def delete_bak_files_recursive(root_dir):
    """递归遍历目录，删除所有package.json.bak文件（无_driver限制）"""
    print("\n" + "=" * 80)
    print("开始清理备份文件（.bak）")
    print("=" * 80)

    delete_success = 0
    delete_fail = 0
    fail_files = []

    # 递归遍历所有目录
    for dir_path, _, _ in os.walk(root_dir):
        # 跳过隐藏目录
        if os.path.basename(dir_path).startswith('.'):
            continue

        bak_file_path = os.path.join(dir_path, "package.json.bak")
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
    """修改单个package.json文件，增强JSON解析容错性"""
    # 1. 备份原文件
    backup_success, backup_msg = backup_file(package_json_path)
    if not backup_success:
        return False, f"【备份失败】{package_json_path} - {backup_msg}"

    # 2. 读取并解析原文件（增强容错）
    try:
        with open(package_json_path, "r", encoding="utf-8") as f:
            content = f.read()
            # 移除UTF-8 BOM头（解决常见解析错误）
            if content.startswith('\ufeff'):
                content = content[1:]
            original_data = json.loads(content)
    except json.JSONDecodeError as e:
        # 提供更详细的解析错误信息
        error_detail = f"JSON格式错误: 行{e.lineno}列{e.colpos} - {str(e)}"
        return False, f"【解析失败】{package_json_path} - {error_detail}"
    except Exception as e:
        return False, f"【读取失败】{package_json_path} - {str(e)}"

    # 3. 构建新的JSON结构（去掉_driver硬编码）
    new_data = {}

    # 保留核心字段（无_driver替换）
    dir_name = os.path.basename(os.path.dirname(package_json_path))
    new_data["name"] = original_data.get("name", dir_name)
    new_data["version"] = original_data.get("version", "1.0.0")
    new_data["description"] = original_data.get("description",
                                                f"A MicroPython library for {new_data['name']} module")
    new_data["author"] = original_data.get("author", "unknown")

    # 新增固定字段
    new_data["license"] = "MIT"
    new_data["chips"] = "all"
    new_data["fw"] = "all"
    new_data["_comments"] = {
        "chips": "该包支持运行的芯片型号，all表示无芯片限制",
        "fw": "该包依赖的特定固件如ulab、lvgl,all表示无固件依赖"
    }

    # 4. 处理urls字段（兼容数组/对象两种格式）
    original_urls = original_data.get("urls", [])
    new_urls = []
    errors = []

    if original_urls:
        for idx, url_entry in enumerate(original_urls):
            # 兼容对象格式（src/dest）和数组格式（[source, target]）
            if isinstance(url_entry, dict) and "src" in url_entry and "dest" in url_entry:
                source_file = url_entry["src"]
                target_path = url_entry["dest"]
            elif isinstance(url_entry, list) and len(url_entry) == 2:
                source_file, target_path = url_entry
            else:
                errors.append(f"条目{idx + 1}格式不正确: {url_entry}")
                continue

            # 从原路径中提取.py文件的上一级目录名
            parent_dir = extract_parent_dir_from_url(target_path)
            if parent_dir:
                new_target = f"{parent_dir}/{source_file}"
            else:
                new_target = source_file  # 如果在根目录，直接用文件名
            new_urls.append([source_file, new_target])
    else:
        # 无urls时，用目录名兜底（去掉_driver依赖）
        default_file = f"{new_data['name']}.py"
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


def batch_modify_package_json_recursive(project_root):
    """递归批量修改所有目录下的package.json（无_driver限制）"""
    print("=" * 80)
    print("开始批量修改package.json文件（支持任意深度目录）")
    print(f"项目根目录：{project_root}")
    print("=" * 80)

    success_count = 0
    fail_count = 0
    total_count = 0
    fail_list = []

    # 递归遍历所有目录
    for dir_path, _, _ in os.walk(project_root):
        # 跳过隐藏目录
        if os.path.basename(dir_path).startswith('.'):
            continue

        package_json_path = os.path.join(dir_path, "package.json")
        if not os.path.exists(package_json_path):
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

    # 调用删除bak文件的函数（递归版）
    delete_bak_files_recursive(project_root)


if __name__ == "__main__":
    # 获取脚本所在目录作为项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    # 执行递归批量修改
    batch_modify_package_json_recursive(project_root)