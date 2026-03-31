# Python env   : Python v3.12.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/06 下午6:36
# @Author  : 李清水
# @File    : list_package_info.py
# @Description : MicroPython代码规范检查工具，自动化校验驱动文件和main.py是否符合8条预设编码规范，支持单文件、多文件及目录（递归/非递归）批量检查

"""
    Pre-commit code checker for MicroPython driver files & main.py
    Check all specified rules:
    1. 非main.py文件:必须包含4个顶层全局变量(__version__, __author__, __license__, __platform__)
    2. 非main.py文件:必须包含独立的 # @License : MIT 注释行
    3. 所有文件:raise/print中无中文字符
    4. main.py:全局变量区无实例化，初始化配置区有实例化
    5. main.py:while循环仅在主程序区
    6. main.py:初始化配置区有time.sleep(3)和FreakStudio打印（非main.py跳过）
    7. 所有文件:__init__方法有参数类型注解+try-except
    8. 非main.py文件:类中所有有入口参数的方法必须包含参数合法性校验（isinstance/hasattr/取值判断+raise）
"""

# ======================================== 导入相关模块 =========================================

import argparse
import re
import ast
from pathlib import Path

# ======================================== 全局变量 ============================================

REQUIRED_GLOBALS = ["__version__", "__author__", "__license__", "__platform__"]
LICENSE_COMMENT = "# @License : MIT"
FREAKSTUDIO_PATTERN = r'print\("FreakStudio: .*"\)'
SLEEP3_PATTERN = r"time\.sleep\(3\)"
MAIN_SECTION_MARKER = "# ========================================  主程序  ============================================"
INIT_CONFIG_MARKER = "# ======================================== 初始化配置 ==========================================="
CHINESE_CHAR_PATTERN = re.compile(r"[\u4e00-\u9fff]")  # 匹配中文字符
# 精准匹配实例化:包含模块.类(如machine.UART)、变量=类(如sensor=TestSensor)
MACHINE_INSTANCE_PATTERNS = [
    r"\w+\.\w+\(",  # 匹配 machine.UART(1) 这类
    r"\w+ = \w+\(",  # 匹配 sensor = TestSensor(5) 这类
    r"\w+ = \w+\.\w+\(",  # 匹配 uart = machine.UART(1) 这类
]

# ======================================== 功能函数 ============================================


def read_file_content(file_path: Path) -> str:
    """
    读取文件内容（UTF-8编码）
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"[FAIL] Error reading file {file_path}: {str(e)}")
        return ""


def check_required_globals(content: str, file_path: Path) -> bool:
    """
    检查4个必填全局变量是否存在（仅非main.py文件需要检查）
    """
    if file_path.name == "main.py":
        print(f"[PASS] {file_path}: main.py Skip global variables check (main.py)")
        return True

    try:
        tree = ast.parse(content)
    except Exception as e:
        print(f"[FAIL] {file_path}: Failed to parse code AST: {str(e)}")
        return False

    missing_vars = []
    for var_name in REQUIRED_GLOBALS:
        found = False
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == var_name:
                        found = True
                        break
        if not found:
            missing_vars.append(var_name)

    if missing_vars:
        print(f"[FAIL] {file_path}: Missing required global variables: {', '.join(missing_vars)}")
        return False
    print(f"[PASS] {file_path}: All 4 required global variables exist")
    return True


def check_license_comment(content: str, file_path: Path) -> bool:
    """
    精准匹配独立的 # @License : MIT 注释行（仅非main.py文件需要检查）
    """
    if file_path.name == "main.py":
        print(f"[PASS] {file_path}: Skip License comment check (main.py)")
        return True

    lines = [line.strip() for line in content.split("\n")]
    if LICENSE_COMMENT.strip() in lines:
        print(f"[PASS] {file_path}: # @License : MIT comment exists")
        return True
    print(f"[FAIL] {file_path}: Missing # @License : MIT comment")
    return False


def check_no_chinese_in_raise_print(content: str, file_path: Path) -> bool:
    """
    检查raise/print中的中文字符（所有文件都检查）
    """
    lines = content.split("\n")
    error_lines = []
    for line_num, line in enumerate(lines, 1):
        if "raise" in line or "print(" in line:
            str_matches = re.findall(r'"([^"]*)"|\'([^\']*)\'', line)
            for match in str_matches:
                str_content = match[0] or match[1]
                if CHINESE_CHAR_PATTERN.search(str_content):
                    error_lines.append(line_num)

    if error_lines:
        print(f"[FAIL] {file_path}: Chinese characters found in raise/print (lines: {', '.join(map(str, error_lines))})")
        return False
    print(f"[PASS] {file_path}: No Chinese in raise/print messages")
    return True


def extract_section_content(content: str, marker: str) -> str:
    """
    精准提取指定分隔注释后的模块内容
    """
    lines = content.split("\n")
    section_start = -1
    section_end = -1

    for idx, line in enumerate(lines):
        if line.strip() == marker.strip():
            section_start = idx + 1
            for jdx in range(section_start, len(lines)):
                jdx_line = lines[jdx].strip()
                if jdx_line.startswith("# ========================================") and jdx_line.endswith(
                    "==========================================="
                ):
                    section_end = jdx
                    break
            break

    if section_start != -1 and section_end != -1:
        return "\n".join(lines[section_start:section_end])
    return ""


def check_init_config_section(content: str, file_path: Path) -> bool:
    """
    检查初始化配置区（仅main.py需要检查，非main.py跳过）
    """
    if file_path.name != "main.py":
        print(f"[PASS] {file_path}: Skip init config section check (non-main.py file)")
        return True

    init_content = extract_section_content(content, INIT_CONFIG_MARKER)
    has_sleep3 = bool(re.search(r"\btime\.sleep\(3\)\b", init_content))
    has_freakstudio = bool(re.search(r'\bprint\("FreakStudio: [^"]*"\)\b', init_content))

    errors = []
    if not has_sleep3:
        errors.append("time.sleep(3)")
    if not has_freakstudio:
        errors.append('print("FreakStudio: xxx")')

    if errors:
        print(f"[FAIL] {file_path}: Init config section missing: {', '.join(errors)}")
        return False
    print(f"[PASS] {file_path}: Init config section has required content")
    return True


def check_main_py_instance_location(content: str, file_path: Path) -> bool:
    """
    精准检查main.py实例化位置（仅main.py需要检查）
    """
    if "main.py" not in str(file_path):
        print(f"[PASS] {file_path}: Skip instantiation location check (non-main.py file)")
        return True

    global_content = extract_section_content(
        content, "# ======================================== 全局变量 ============================================"
    )
    init_content = extract_section_content(content, INIT_CONFIG_MARKER)

    global_has_instance = False
    for pattern in MACHINE_INSTANCE_PATTERNS:
        if re.search(pattern, global_content):
            global_has_instance = True
            break

    init_has_instance = False
    for pattern in MACHINE_INSTANCE_PATTERNS:
        if re.search(pattern, init_content):
            init_has_instance = True
            break

    errors = []
    if global_has_instance:
        errors.append("Instance found in global variables section (invalid)")
    if not init_has_instance:
        errors.append("No instance found in init config section (required)")

    if errors:
        print(f"[FAIL] {file_path}: {'; '.join(errors)}")
        return False
    print(f"[PASS] {file_path}: main.py instance location is correct")
    return True


def check_main_py_while_loop(content: str, file_path: Path) -> bool:
    """
    精准检查while循环仅在主程序区（仅main.py需要检查）
    修复：1.while正则匹配所有写法 2.全覆盖主程序区后代码
    """
    if file_path.name != "main.py":
        print(f"[PASS] {file_path}: Skip while loop location check (non-main.py file)")
        return True

    lines = content.split("\n")
    main_start_idx = -1
    # 定位主程序分隔符
    for idx, line in enumerate(lines):
        if line.strip() == MAIN_SECTION_MARKER.strip():
            main_start_idx = idx
            break

    # 划分区域：非主程序区 = 分隔符前所有代码；主程序区 = 分隔符后所有代码
    non_main_content = "\n".join(lines[:main_start_idx]) if main_start_idx != -1 else content
    main_content = "\n".join(lines[main_start_idx:]) if main_start_idx != -1 else ""

    # 通用正则：匹配所有合法while循环（修复正则局限问题）
    while_pattern = re.compile(r"^\s*while\s+", re.MULTILINE)
    while_in_non_main = bool(while_pattern.search(non_main_content))
    while_in_main = bool(while_pattern.search(main_content))
    has_any_while = bool(while_pattern.search(content))

    # 校验规则
    if while_in_non_main:
        print(f"[FAIL] {file_path}: while loop found outside main program section (invalid)")
        return False
    if has_any_while and not while_in_main:
        print(f"[FAIL] {file_path}: while loop not found in main program section (required)")
        return False

    print(f"[PASS] {file_path}: main.py while loop location is correct")
    return True

def check_type_hints_and_try_except(content: str, file_path: Path) -> bool:
    """
    检查__init__方法的参数类型注解（仅检查类型注解，移除try-except检查）
    """
    try:
        tree = ast.parse(content)
    except Exception as e:
        print(f"[FAIL] {file_path}: Failed to parse code AST for type check: {str(e)}")
        return False

    has_type_hints = False
    has_init_method = False

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "__init__":
            has_init_method = True
            # 仅检查类型注解（移除try-except检查）
            for arg in node.args.args:
                if hasattr(arg, "annotation") and arg.annotation:
                    has_type_hints = True

    # 无__init__方法则跳过检查
    if not has_init_method:
        print(f"[PASS] {file_path}: Skip type hint check (no init method)")
        return True

    # 仅校验类型注解
    if not has_type_hints:
        print(f"[FAIL] {file_path}: No type hints found in __init__ parameters")
        return False
    print(f"[PASS] {file_path}: Type hints exist in __init__ parameters")
    return True


def check_method_param_validation(content: str, file_path: Path) -> bool:
    """
    检查非main.py文件中类的所有有参数方法是否包含参数合法性校验（isinstance/hasattr/取值判断+raise）
    """
    # main.py跳过该检查
    if file_path.name == "main.py":
        print(f"[PASS] {file_path}: Skip method parameter validation check (main.py)")
        return True

    try:
        tree = ast.parse(content)
    except Exception as e:
        print(f"[FAIL] {file_path}: Failed to parse code AST for param check: {str(e)}")
        return False

    # 存储缺少参数校验的方法
    missing_validation_methods = []

    # 遍历所有类
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            # 遍历类中的所有方法
            for func in node.body:
                if isinstance(func, ast.FunctionDef):
                    func_name = func.name
                    # 获取方法参数（排除self/cls）
                    args = [arg.arg for arg in func.args.args if arg.arg not in ["self", "cls"]]
                    if not args:  # 无入口参数，跳过
                        continue

                    # 检查方法体是否包含参数校验逻辑
                    has_validation = False
                    # 遍历方法体所有节点
                    for stmt in ast.walk(func):
                        # 1. 检查是否有isinstance判断 + raise
                        if isinstance(stmt, ast.If):
                            # 检查条件是否包含isinstance/hasattr/取值判断
                            cond = stmt.test
                            has_isinstance = False
                            has_hasattr = False
                            has_value_check = False

                            # 检查isinstance调用
                            if isinstance(cond, ast.Call) and isinstance(cond.func, ast.Name) and cond.func.id == "isinstance":
                                has_isinstance = True
                            # 检查hasattr调用
                            elif isinstance(cond, ast.Call) and isinstance(cond.func, ast.Name) and cond.func.id == "hasattr":
                                has_hasattr = True
                            # 检查取值范围判断（==/!=/>/<等）
                            elif isinstance(cond, (ast.Compare, ast.BoolOp)):
                                has_value_check = True

                            # 检查if块内是否有raise
                            has_raise = False
                            for body_stmt in stmt.body:
                                if isinstance(body_stmt, ast.Raise):
                                    has_raise = True
                                    break

                            if (has_isinstance or has_hasattr or has_value_check) and has_raise:
                                has_validation = True
                                break

                    if not has_validation:
                        missing_validation_methods.append(f"{class_name}.{func_name}")

    if missing_validation_methods:
        print(f"[FAIL] {file_path}: Methods missing parameter validation: {', '.join(missing_validation_methods)}")
        return False
    print(f"[PASS] {file_path}: All methods with parameters have valid parameter validation")
    return True


def check_file(file_path: Path) -> bool:
    """
    全量检查单个文件
    """
    content = read_file_content(file_path)
    if not content:
        return False

    checks = [
        check_required_globals,
        check_license_comment,
        check_no_chinese_in_raise_print,
        check_init_config_section,
        check_main_py_instance_location,
        check_main_py_while_loop,
        check_type_hints_and_try_except,
        check_method_param_validation,  # 新增:方法参数校验检查
    ]

    all_passed = True
    for check_func in checks:
        if not check_func(content, file_path):
            all_passed = False

    return all_passed


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================


def main():
    """
    命令行入口:支持两种模式
    1. 传入文件路径:检查指定.py文件（原有功能）
    2. 传入目录路径:检查目录下所有.py文件（新增功能）
    可选参数:-r/--recursive 递归遍历子文件夹（默认不递归）
    """
    parser = argparse.ArgumentParser(description="Check MicroPython code rules")
    # 位置参数:支持传入文件/目录路径（可多个）
    parser.add_argument("paths", nargs="+", help="File path or directory path (supports multiple)")
    # 可选参数:是否递归遍历子文件夹
    parser.add_argument("-r", "--recursive", action="store_true", help="Recursively traverse all subfolders (only for directory paths)")

    args = parser.parse_args()

    # 存储所有待检查的.py文件路径
    py_files = []
    # 遍历所有传入的路径（文件/目录）
    for path_str in args.paths:
        path = Path(path_str)
        # 处理路径不存在的情况
        if not path.exists():
            print(f"[ERROR] Path does not exist:{path_str}")
            exit(1)

        # 情况1:传入的是文件，且是.py文件 → 加入列表
        if path.is_file() and path.suffix == ".py":
            py_files.append(path)
        # 情况2:传入的是文件，但不是.py文件 → 跳过并提示
        elif path.is_file() and path.suffix != ".py":
            print(f"[WARNING] Skip non-.py file:{path_str}")
        # 情况3:传入的是目录 → 遍历目录下的.py文件
        elif path.is_dir():
            if args.recursive:
                # 递归遍历目录下所有.py文件
                py_files.extend(Path(path).rglob("*.py"))
            else:
                # 仅遍历目录下直接的.py文件（不递归子文件夹）
                py_files.extend(Path(path).glob("*.py"))

    # 去重（避免重复检查同一文件）
    py_files = list(set(py_files))
    if not py_files:
        print("[ERROR] No .py files found to check")
        exit(1)

    # 批量检查所有.py文件
    passed = True
    failed_files = []
    print(f"[INFO] Found {len(py_files)} .py files, starting check...\n")
    for file_path in py_files:
        print(f"	[DOING] Checking file:{file_path}")
        if not check_file(file_path):
            passed = False
            failed_files.append(str(file_path))
        print("-" * 80)  # 分隔线

    # 输出汇总结果
    print("\n[DONE] [SUMMARY] Check summary:")
    print(f"Total files:{len(py_files)}")
    print(f"Passed:{len(py_files) - len(failed_files)}")
    print(f"Failed:{len(failed_files)}")
    if failed_files:
        print(f"\n[FAIL] Files with failed checks:")
        for f in failed_files:
            print(f"  - {f}")
        exit(1)
    else:
        print("\n[PASS] All files passed checks!")
        exit(0)


if __name__ == "__main__":
    main()
