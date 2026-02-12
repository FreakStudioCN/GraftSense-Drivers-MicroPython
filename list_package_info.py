# Python env   : Python v3.12.0
# -*- coding: utf-8 -*-
# @Time    : 2026/2/12 下午6:36
# @Author  : 李清水
# @File    : list_package_info.py
# @Description : 扫描并列出项目中所有package.json文件及urls配置信息

import os
import json
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext

def scan_package_json(project_root):
    """扫描项目目录，收集所有package.json的信息（包含字段核验）"""
    package_info = []
    # 定义必须包含的核心字段
    required_fields = ["name", "version", "description", "author"]

    # 遍历项目根目录下的所有子目录
    for entry in os.scandir(project_root):
        if entry.is_dir() and not entry.name.startswith('.'):  # 跳过隐藏文件夹
            subdir_name = entry.name
            subdir_path = entry.path

            # 遍历子目录下的驱动文件夹（以 _driver 结尾）
            for driver_folder in os.listdir(subdir_path):
                driver_path = os.path.join(subdir_path, driver_folder)
                if not os.path.isdir(driver_path) or not driver_folder.endswith("_driver"):
                    continue

                # 检查package.json是否存在
                package_json_path = os.path.join(driver_path, "package.json")
                driver_info = {
                    "subdir": subdir_name,
                    "driver_folder": driver_folder,
                    "package_path": package_json_path,
                    "name": "未知名称",
                    "version": "未知版本",
                    "description": "无描述",
                    "author": "未知作者",
                    "urls": [],
                    "error": "",
                    "missing_fields": []  # 新增：记录缺失的必要字段
                }

                if not os.path.exists(package_json_path):
                    driver_info["error"] = "无package.json文件"
                    package_info.append(driver_info)
                    continue

                # 读取并解析package.json
                try:
                    with open(package_json_path, "r", encoding="utf-8") as f:
                        package_data = json.load(f)

                    # 核验必要字段
                    missing_fields = []
                    for field in required_fields:
                        if field not in package_data or package_data[field] is None or package_data[field] == "":
                            missing_fields.append(field)

                    driver_info["missing_fields"] = missing_fields

                    # 填充字段值（无则用默认值）
                    driver_info["name"] = package_data.get("name", "未知名称")
                    driver_info["version"] = package_data.get("version", "未知版本")
                    driver_info["description"] = package_data.get("description", "无描述")
                    driver_info["author"] = package_data.get("author", "未知作者")
                    driver_info["urls"] = package_data.get("urls", [])

                except json.JSONDecodeError as e:
                    driver_info["error"] = f"JSON解析错误: {str(e)}"
                except Exception as e:
                    driver_info["error"] = f"读取文件错误: {str(e)}"

                package_info.append(driver_info)

    return package_info


def on_double_click(tree, log_text):
    """处理树形节点双击事件，打开对应的package.json文件"""
    try:
        # 获取选中的节点
        selected_item = tree.selection()[0]
        item_text = tree.item(selected_item, "text")
        item_values = tree.item(selected_item, "values")

        package_path = None

        # 场景1：双击的是package.json节点
        if item_text == "package.json" and len(item_values) >= 2:
            value_str = item_values[1]
            # 提取纯路径（去掉错误信息）
            if "(错误:" in value_str:
                package_path = value_str.split(" (错误:")[0].strip()
            else:
                package_path = value_str.strip()

        # 场景2：双击的是package.json的子节点（name/version/urls等），向上找父节点
        else:
            parent_item = selected_item
            # 向上遍历直到找到package.json节点
            while parent_item:
                parent_text = tree.item(parent_item, "text")
                if parent_text == "package.json":
                    parent_values = tree.item(parent_item, "values")
                    value_str = parent_values[1]
                    if "(错误:" in value_str:
                        package_path = value_str.split(" (错误:")[0].strip()
                    else:
                        package_path = value_str.strip()
                    break
                # 获取上一级父节点
                parent_item = tree.parent(parent_item)

        # 验证路径并打开文件
        if package_path:
            if os.path.exists(package_path):
                # 跨平台打开文件（优先适配Windows）
                if sys.platform == "win32":
                    os.startfile(package_path)  # Windows直接打开
                else:
                    # Mac/Linux兼容
                    import subprocess
                    subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", package_path])

                # 日志记录成功
                log_text.insert(tk.END, f"\n✅ 已打开文件: {package_path}\n", "normal")
                log_text.see(tk.END)
            else:
                # 文件不存在
                log_text.insert(tk.END, f"\n❌ 打开失败：文件不存在 → {package_path}\n", "warning")
                log_text.see(tk.END)
        else:
            # 未找到package.json路径
            log_text.insert(tk.END, "\n⚠️  请双击package.json节点或其子节点来打开文件\n", "warning")
            log_text.see(tk.END)

    except IndexError:
        # 未选中任何节点
        log_text.insert(tk.END, "\n⚠️  请先选中一个节点再双击\n", "warning")
        log_text.see(tk.END)
    except Exception as e:
        # 其他异常（如权限不足）
        log_text.insert(tk.END, f"\n❌ 打开文件失败: {str(e)}\n", "warning")
        log_text.see(tk.END)


def create_gui(project_root):
    """创建可视化UI界面（带红字警告+双击打开文件）"""
    # 主窗口配置
    root = tk.Tk()
    root.title("传感器驱动 package.json 信息查看器（带字段核验+双击打开）")
    root.geometry("1200x800")  # 窗口大小
    root.minsize(1000, 700)

    # 创建顶部说明标签
    info_label = tk.Label(
        root,
        text=f"项目根目录: {project_root}\n⚠️  红字为缺失必要字段警告 | 必要字段：name、version、description、author\n💡 双击package.json节点/其子节点可直接打开文件",
        font=("微软雅黑", 10),
        justify=tk.LEFT,
        padx=10,
        pady=5,
        fg="red"
    )
    info_label.pack(fill=tk.X)

    # 创建树形结构控件
    tree_frame = ttk.Frame(root)
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    # 树形结构列配置
    columns = ("类型", "字段/内容")
    tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings", height=25)
    tree.heading("类型", text="类型")
    tree.heading("字段/内容", text="字段/内容/路径")

    # 设置列宽
    tree.column("类型", width=180, anchor=tk.CENTER)
    tree.column("字段/内容", width=800, anchor=tk.W)

    # 添加滚动条
    vscroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
    hscroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=tree.xview)
    tree.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)

    # 布局树形结构和滚动条
    tree.grid(row=0, column=0, sticky="nsew")
    vscroll.grid(row=0, column=1, sticky="ns")
    hscroll.grid(row=1, column=0, sticky="ew")
    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)

    # 绑定双击事件
    tree.bind("<Double-1>", lambda e: on_double_click(tree, log_text))

    # 底部日志区域
    log_frame = ttk.LabelFrame(root, text="扫描日志（红字为警告）")
    log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    log_text = scrolledtext.ScrolledText(log_frame, font=("Consolas", 9))
    log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    # 配置红字标签（用于警告输出）
    log_text.tag_configure("warning", foreground="red", font=("Consolas", 9, "bold"))
    log_text.tag_configure("normal", foreground="black", font=("Consolas", 9))

    # 扫描并填充树形结构
    def fill_tree():
        log_text.insert(tk.END, f"开始扫描项目目录: {project_root}\n", "normal")
        log_text.see(tk.END)
        root.update()

        package_info = scan_package_json(project_root)

        # 按子目录分组
        subdir_groups = {}
        for info in package_info:
            subdir = info["subdir"]
            if subdir not in subdir_groups:
                subdir_groups[subdir] = []
            subdir_groups[subdir].append(info)

        # 填充树形结构
        for subdir, drivers in subdir_groups.items():
            # 添加子目录节点
            subdir_node = tree.insert("", tk.END, text=subdir, values=("子目录", subdir))

            for driver_info in drivers:
                driver_name = driver_info["driver_folder"]
                # 基础日志输出
                log_text.insert(tk.END, f"\n正在扫描: {driver_name}\n", "normal")
                log_text.see(tk.END)
                root.update()

                # 添加驱动文件夹节点
                driver_node = tree.insert(
                    subdir_node, tk.END,
                    text=driver_name,
                    values=("驱动文件夹", driver_name)
                )

                # 添加package.json节点
                if driver_info["error"]:
                    package_node = tree.insert(
                        driver_node, tk.END,
                        text="package.json",
                        values=("配置文件", f"{driver_info['package_path']} (错误: {driver_info['error']})")
                    )
                    log_text.insert(tk.END, f"⚠️  {driver_name}: {driver_info['error']}\n", "warning")
                else:
                    package_node = tree.insert(
                        driver_node, tk.END,
                        text="package.json",
                        values=("配置文件", driver_info["package_path"])
                    )

                    # 检查是否缺失必要字段
                    if driver_info["missing_fields"]:
                        missing_str = ", ".join(driver_info["missing_fields"])
                        # 红字输出缺失字段警告
                        log_text.insert(tk.END, f"❌ {driver_name}: 缺失必要字段 → {missing_str}\n", "warning")
                        # 在树形节点标注缺失字段
                        tree.insert(
                            package_node, tk.END,
                            text="⚠️  字段警告",
                            values=("警告", f"缺失必要字段：{missing_str}")
                        )

                    # 添加核心字段节点
                    tree.insert(
                        package_node, tk.END,
                        text="name",
                        values=("核心字段", driver_info["name"])
                    )
                    tree.insert(
                        package_node, tk.END,
                        text="version",
                        values=("核心字段", driver_info["version"])
                    )
                    tree.insert(
                        package_node, tk.END,
                        text="description",
                        values=("核心字段", driver_info["description"])
                    )
                    tree.insert(
                        package_node, tk.END,
                        text="author",
                        values=("核心字段", driver_info["author"])
                    )

                    # 添加urls节点
                    urls_node = tree.insert(package_node, tk.END, text="urls", values=("核心字段", "文件映射列表"))

                    # 添加urls条目
                    if not driver_info["urls"]:
                        tree.insert(urls_node, tk.END, text="空", values=("条目", "无urls配置"))
                        log_text.insert(tk.END, f"⚠️  {driver_name}: 无urls配置\n", "warning")
                    else:
                        for idx, url_entry in enumerate(driver_info["urls"]):
                            if len(url_entry) == 2:
                                source, target = url_entry
                                entry_text = f"条目{idx + 1}: {source} → {target}"
                            else:
                                entry_text = f"条目{idx + 1}: 格式错误 {url_entry}"
                                log_text.insert(tk.END, f"⚠️  {driver_name}: urls条目{idx + 1}格式错误\n", "warning")
                            tree.insert(urls_node, tk.END, text=f"条目{idx + 1}", values=("条目", entry_text))

                log_text.insert(tk.END, f"✅ 完成扫描: {driver_name}\n", "normal")
                log_text.see(tk.END)
                root.update()

        log_text.insert(tk.END, "\n================ 扫描完成 ================\n", "normal")
        log_text.see(tk.END)

    # 启动扫描
    fill_tree()

    # 运行主循环
    root.mainloop()


if __name__ == "__main__":
    # 获取脚本所在目录作为项目根目录（无需手动修改）
    project_root = os.path.dirname(os.path.abspath(__file__))
    create_gui(project_root)