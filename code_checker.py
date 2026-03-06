#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pre-commit code checker for MicroPython driver files & main.py
Check all specified rules:
1. 4 required global variables (__version__, __author__, __license__, __platform__)
2. # @License : MIT comment exists
3. No Chinese in raise/print messages
4. main.py: no instance in global vars (move to init config)
5. main.py: while loop only in main program section
6. Init config section has time.sleep(3) and FreakStudio print
7. Entry params have try-except check
8. Type hints are included
"""
import argparse
import re
import astroid

# 修复：移除多余的Annotation导入，仅保留用到的类
from astroid.nodes import Assign, Name, FunctionDef, Try

from pathlib import Path

# -------------------------- 配置常量（可根据需求调整） --------------------------
REQUIRED_GLOBALS = ["__version__", "__author__", "__license__", "__platform__"]
LICENSE_COMMENT = "# @License : MIT"
FREAKSTUDIO_PATTERN = r'print\("FreakStudio: .*"\)'
SLEEP3_PATTERN = r"time\.sleep\(3\)"
MAIN_SECTION_MARKER = "# ========================================  主程序  ============================================"
INIT_CONFIG_MARKER = "# ======================================== 初始化配置 ==========================================="
CHINESE_CHAR_PATTERN = re.compile(r"[\u4e00-\u9fff]")  # 匹配中文字符
# 匹配machine实例/类实例化（如machine.UART(1)、sensor = DS18B20(16)）
MACHINE_INSTANCE_PATTERNS = [r"machine\.\w+\(", r"\w+ = \w+\("]


# -------------------------- 核心工具函数 --------------------------
def read_file_content(file_path: Path) -> str:
    """
    读取文件内容（UTF-8编码）
    :param file_path: 待检查文件路径
    :return: 文件文本内容，读取失败返回空字符串
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"❌ Error reading file {file_path}: {str(e)}")
        return ""


def check_required_globals(content: str, file_path: Path) -> bool:
    """
    检查4个必填全局变量是否存在（修复astroid导入问题）
    :param content: 文件内容
    :param file_path: 文件路径（用于错误提示）
    :return: True=存在所有变量，False=缺失
    """
    try:
        tree = astroid.parse(content)
    except Exception as e:
        print(f"❌ {file_path}: Failed to parse code AST: {str(e)}")
        return False

    missing_vars = []
    for var_name in REQUIRED_GLOBALS:
        found = False
        # 修复：使用从nodes导入的Assign/Name
        for node in tree.body:
            if isinstance(node, Assign):
                for target in node.targets:
                    if isinstance(target, Name) and target.name == var_name:
                        found = True
                        break
        if not found:
            missing_vars.append(var_name)

    if missing_vars:
        print(f"❌ {file_path}: Missing required global variables: {', '.join(missing_vars)}")
        return False
    print(f"✅ {file_path}: All 4 required global variables exist")
    return True


def check_license_comment(content: str, file_path: Path) -> bool:
    """
    检查是否包含固定注释 # @License : MIT
    :param content: 文件内容
    :param file_path: 文件路径
    :return: True=存在，False=缺失
    """
    if LICENSE_COMMENT in content:
        print(f"✅ {file_path}: # @License : MIT comment exists")
        return True
    print(f"❌ {file_path}: Missing # @License : MIT comment")
    return False


def check_no_chinese_in_raise_print(content: str, file_path: Path) -> bool:
    """
    检查raise/print语句中是否包含中文字符
    :param content: 文件内容
    :param file_path: 文件路径
    :return: True=无中文，False=有中文
    """
    lines = content.split("\n")
    error_lines = []
    for line_num, line in enumerate(lines, 1):
        # 仅检查包含raise/print的行
        if "raise" in line or "print(" in line:
            # 提取字符串内容（匹配双引号/单引号包裹的内容）
            str_matches = re.findall(r'"([^"]*)"|\'([^\']*)\'', line)
            for match in str_matches:
                str_content = match[0] or match[1]
                if CHINESE_CHAR_PATTERN.search(str_content):
                    error_lines.append(line_num)

    if error_lines:
        print(f"❌ {file_path}: Chinese characters found in raise/print (lines: {', '.join(map(str, error_lines))})")
        return False
    print(f"✅ {file_path}: No Chinese in raise/print messages")
    return True


def check_init_config_section(content: str, file_path: Path) -> bool:
    """
    检查初始化配置模块是否包含 time.sleep(3) 和 print("FreakStudio: xxx")
    :param content: 文件内容
    :param file_path: 文件路径
    :return: True=满足，False=缺失
    """
    # 分割代码模块（按分隔注释拆分）
    section_markers = re.findall(r"# ======================================== .* ===========================================", content)
    section_contents = re.split(r"# ======================================== .* ===========================================", content)

    init_config_content = ""
    # 定位初始化配置模块内容
    for idx, marker in enumerate(section_markers):
        if INIT_CONFIG_MARKER in marker:
            if idx + 1 < len(section_contents):
                init_config_content = section_contents[idx + 1]
            break

    # 检查强制内容
    has_sleep3 = re.search(SLEEP3_PATTERN, init_config_content) is not None
    has_freakstudio = re.search(FREAKSTUDIO_PATTERN, init_config_content) is not None

    errors = []
    if not has_sleep3:
        errors.append("time.sleep(3)")
    if not has_freakstudio:
        errors.append('print("FreakStudio: xxx")')

    if errors:
        print(f"❌ {file_path}: Init config section missing: {', '.join(errors)}")
        return False
    print(f"✅ {file_path}: Init config section has required content")
    return True


def check_main_py_instance_location(content: str, file_path: Path) -> bool:
    """
    检查main.py：全局变量区无实例化，初始化配置区有实例化
    :param content: 文件内容
    :param file_path: 文件路径
    :return: True=合规，False=违规（非main.py直接返回True）
    """
    if "main.py" not in str(file_path):
        return True

    # 分割全局变量区和初始化配置区
    section_markers = re.findall(r"# ======================================== .* ===========================================", content)
    section_contents = re.split(r"# ======================================== .* ===========================================", content)

    global_vars_content = ""
    init_config_content = ""
    # 提取对应模块内容
    for idx, marker in enumerate(section_markers):
        if "# ======================================== 全局变量 ============================================" in marker:
            if idx + 1 < len(section_contents):
                global_vars_content = section_contents[idx + 1]
        elif INIT_CONFIG_MARKER in marker:
            if idx + 1 < len(section_contents):
                init_config_content = section_contents[idx + 1]

    # 检查全局变量区是否有实例化
    global_has_instance = False
    for pattern in MACHINE_INSTANCE_PATTERNS:
        if re.search(pattern, global_vars_content):
            global_has_instance = True
            break

    # 检查初始化配置区是否有实例化
    init_has_instance = False
    for pattern in MACHINE_INSTANCE_PATTERNS:
        if re.search(pattern, init_config_content):
            init_has_instance = True
            break

    errors = []
    if global_has_instance:
        errors.append("Instance found in global variables section")
    if not init_has_instance:
        errors.append("No instance found in init config section")

    if errors:
        print(f"❌ {file_path}: {'; '.join(errors)}")
        return False
    print(f"✅ {file_path}: main.py instance location is correct")
    return True


def check_main_py_while_loop(content: str, file_path: Path) -> bool:
    """
    检查main.py：while循环仅出现在主程序模块下
    :param content: 文件内容
    :param file_path: 文件路径
    :return: True=合规，False=违规（非main.py直接返回True）
    """
    if "main.py" not in str(file_path):
        return True

    # 分割主程序模块
    sections = re.split(MAIN_SECTION_MARKER, content)
    if len(sections) < 2:
        print(f"❌ {file_path}: Main program section marker not found")
        return False

    main_section_content = sections[1]  # 主程序模块内容
    other_content = sections[0]  # 主程序模块之前的内容

    # 检查while循环位置
    while_in_other = re.search(r"while\s*\(", other_content) is not None
    while_in_main = re.search(r"while\s*\(", main_section_content) is not None

    if while_in_other:
        print(f"❌ {file_path}: while loop found outside main program section")
        return False
    if "while" in content and not while_in_main:
        print(f"❌ {file_path}: while loop not found in main program section")
        return False

    print(f"✅ {file_path}: main.py while loop location is correct")
    return True


def check_type_hints_and_try_except(content: str, file_path: Path) -> bool:
    """
    检查入口参数：__init__方法有类型注解 + try-except校验（修复astroid.walk问题）
    :param content: 文件内容
    :param file_path: 文件路径
    :return: True=满足，False=缺失
    """
    try:
        tree = astroid.parse(content)
    except Exception as e:
        print(f"❌ {file_path}: Failed to parse code AST for type check: {str(e)}")
        return False

    has_type_hints = False
    has_try_except_in_init = False

    # 修复：使用tree.walk()而非astroid.walk(tree)
    for node in tree.walk():
        # 检查__init__方法的参数类型注解
        if isinstance(node, FunctionDef) and node.name == "__init__":
            # 检查参数注解
            for arg in node.args.args:
                if arg.annotation:
                    has_type_hints = True
            # 检查try-except块
            for item in node.body:
                if isinstance(item, Try):
                    has_try_except_in_init = True

    errors = []
    if not has_type_hints:
        errors.append("No type hints found in __init__ parameters")
    if not has_try_except_in_init:
        errors.append("No try-except block found in __init__ method")

    if errors:
        print(f"❌ {file_path}: {'; '.join(errors)}")
        return False
    print(f"✅ {file_path}: Type hints and try-except exist in entry params")
    return True


def check_file(file_path: Path) -> bool:
    """
    对单个文件执行全量规则检查
    :param file_path: 文件路径
    :return: True=所有规则通过，False=至少一个规则失败
    """
    content = read_file_content(file_path)
    if not content:
        return False

    # 执行所有检查项
    checks = [
        check_required_globals,
        check_license_comment,
        check_no_chinese_in_raise_print,
        check_init_config_section,
        check_main_py_instance_location,
        check_main_py_while_loop,
        check_type_hints_and_try_except,
    ]

    all_passed = True
    for check_func in checks:
        if not check_func(content, file_path):
            all_passed = False

    return all_passed


# -------------------------- 命令行入口 --------------------------
def main():
    """命令行入口：接收待检查文件列表，执行检查并返回退出码"""
    parser = argparse.ArgumentParser(description="Check MicroPython code against custom rules")
    parser.add_argument("files", nargs="+", help="Files to check (passed by pre-commit)")
    args = parser.parse_args()

    passed = True
    # 临时修改：检查所有.py文件（测试完成后可改回原逻辑）
    for file in args.files:
        file_path = Path(file)
        if file_path.suffix == ".py":
            if not check_file(file_path):
                passed = False

    # 检查失败返回非0码，触发pre-commit拦截提交
    if not passed:
        exit(1)


if __name__ == "__main__":
    main()
