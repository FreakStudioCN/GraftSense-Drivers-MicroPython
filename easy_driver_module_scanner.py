# Python env   : Python v3.12.0
# -*- coding: utf-8 -*-
# @Time    : 2026/2/12 下午6:36
# @Author  : 李清水
# @File    : driver_module_scanner.py
# @Description : 递归扫描任意深度目录下的所有code文件夹，提取驱动模块名，检查驱动文件数量及类数量，筛选出单驱动文件且仅含单个类的驱动模块

import os
import ast
from pathlib import Path


def count_classes_in_file(file_path: Path) -> int:
    """统计一个Python文件中定义的类的数量"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        tree = ast.parse(code)
        class_count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_count += 1
        return class_count
    except SyntaxError:
        print(f"⚠️  语法错误，无法解析文件: {file_path}")
        return -1  # 标记为解析失败
    except Exception as e:
        print(f"⚠️  读取文件失败 {file_path}: {e}")
        return -1


def check_code_folder(code_dir: Path) -> dict:
    """检查单个code文件夹的驱动文件规则"""
    # 提取code文件夹的直接父文件夹名（驱动模块名）
    module_name = code_dir.parent.name
    # 提取模块的完整路径（便于定位）
    module_path = code_dir.parent

    result = {"module_name": module_name, "module_path": str(module_path), "is_test_module": False, "driver_files": [], "single_class_driver": None}

    # 筛选code下的py文件，排除main.py/demo.py
    py_files = list(code_dir.glob("*.py"))
    driver_files = [f for f in py_files if f.name not in ("main.py", "demo.py")]

    # 判断是否为测试模块（仅含main/demo.py）
    if not driver_files:
        result["is_test_module"] = True
        return result

    # 记录驱动文件列表
    result["driver_files"] = [f.name for f in driver_files]

    # 检查：仅1个驱动文件 + 仅1个类
    if len(driver_files) == 1:
        driver_file = driver_files[0]
        class_count = count_classes_in_file(driver_file)
        if class_count == 1:
            result["single_class_driver"] = {"file": driver_file.name, "file_path": str(driver_file), "class_count": class_count}

    return result


def find_all_code_folders(root_dir: str | Path) -> list[Path]:
    """递归遍历根目录，找到所有名为code的文件夹"""
    root_path = Path(root_dir)
    if not root_path.exists():
        raise ValueError(f"根目录不存在: {root_dir}")

    code_folders = []
    # 递归遍历所有目录
    for dir_path, dir_names, _ in os.walk(root_path):
        # 跳过隐藏目录（如.git、venv）
        if any(part.startswith(".") for part in Path(dir_path).parts):
            continue
        # 找到code文件夹
        if "code" in dir_names:
            code_folder = Path(dir_path) / "code"
            code_folders.append(code_folder)
    return code_folders


def scan_all_drivers(root_dir: str | Path) -> list[dict]:
    """主函数：扫描所有驱动模块"""
    # 1. 递归找到所有code文件夹
    code_folders = find_all_code_folders(root_dir)
    if not code_folders:
        print("⚠️  未找到任何code文件夹")
        return []

    # 2. 检查每个code文件夹的规则
    results = []
    for code_folder in code_folders:
        result = check_code_folder(code_folder)
        results.append(result)
    return results


if __name__ == "__main__":
    # 替换为你的项目根目录（绝对/相对路径都可以）
    ROOT_DIR = r"./"  # Windows示例
    # ROOT_DIR = "/home/user/your_project"  # Linux/Mac示例

    # 执行扫描
    scan_results = scan_all_drivers(ROOT_DIR)

    # 格式化输出结果
    print("=" * 50)
    print("🎯 驱动模块扫描结果（按code文件夹定位）")
    print("=" * 50)
    for idx, res in enumerate(scan_results, 1):
        print(f"\n【{idx}】驱动模块: {res['module_name']}")
        print(f"   模块路径: {res['module_path']}")
        if res["is_test_module"]:
            print(f"   状态: ❌ 测试模块（仅含main/demo.py，无驱动文件）")
        else:
            print(f"   驱动文件: {res['driver_files']}")
            if res["single_class_driver"]:
                print(f"   状态: ✅ 符合要求（单驱动文件+仅1个类）")
                print(f"   详情: {res['single_class_driver']['file']} ({res['single_class_driver']['class_count']}个类)")
            else:
                print(f"   状态: ❌ 不符合要求（多驱动文件/多类）")
