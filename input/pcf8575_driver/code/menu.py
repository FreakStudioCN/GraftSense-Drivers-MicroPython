# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/9/26 下午5:17
# @Author  : 李清水
# @File    : menu.py
# @Description : OLED显示简易菜单库

# ======================================== 导入相关模块 =========================================

# 时间相关的模块
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class MenuNode:
    """
    MenuNode类用于表示菜单中的每个节点，包含菜单名称、回调函数和子菜单。

    该类封装了菜单节点的基本信息，包括名称、进入和退出该菜单时的回调函数，以及子菜单的管理。
    每个菜单节点可以拥有多个子菜单，并且支持递归地查找和管理。

    Attributes:
        name (str): 菜单名称，唯一标识一个菜单节点。
        next (MenuNode): 下一个菜单节点，暂时未使用。
        sub_menu (list): 存储该菜单的所有子菜单节点。
        enter_callback (callable): 进入该菜单时调用的回调函数。
        exit_callback (callable): 退出该菜单时调用的回调函数。

    Methods:
        __init__(self, name:str, enter_callback : callable=None, exit_callback : callable=None):
            初始化MenuNode类实例，设置菜单名称和回调函数。
    """

    def __init__(self, name: str, enter_callback: callable = None, exit_callback: callable = None):
        self.name = name
        self.next = None
        self.sub_menu = []
        self.enter_callback = enter_callback
        self.exit_callback = exit_callback


class SimpleOLEDMenu:
    """
    SimpleOLEDMenu类用于管理和显示基于OLED屏幕的菜单系统。

    该类提供了一个简单的菜单系统，能够在OLED显示屏上显示多层次的菜单。用户可以通过上下选择菜单项并进入子菜单，
    也可以返回上级菜单。菜单支持回调函数，在进入和退出菜单时触发特定的操作。

    Attributes:
        oled (OLED): OLED显示对象，用于显示菜单。
        name (str): 菜单的名称，用于标识菜单。
        x (int): 菜单起始X坐标。
        y (int): 菋单起始Y坐标。
        width (int): 菜单的宽度。
        height (int): 菜单的高度。
        head (MenuNode): 根菜单节点，表示整个菜单的起始点。
        selected_index (int): 当前选中的菜单项索引。
        menu_stack (List[MenuNode]): 存储菜单层次的栈。
        scroll_offset (int): 当前菜单的滚动偏移量。

    Methods:
        __init__(self, oled: OLED, name: str, pos_x: int, pos_y: int, width: int, height: int) -> None:
            初始化SimpleOLEDMenu类实例，设置菜单相关参数。

        add_menu(self, name: str, parent_name: str = None, enter_callback: Callable = None, exit_callback: Callable = None) -> None:
            添加一个新的菜单项，并将其添加到指定的父菜单中。

        _find_node(self, current: MenuNode, name: str) -> Union[MenuNode, None]:
            递归查找菜单中是否存在指定名称的菜单项。

        delete_menu(self, name: str) -> None:
            删除指定名称的菜单项，并更新显示。

        display_menu(self) -> None:
            显示当前菜单，支持滚动显示和选中状态。

        select_down(self) -> None:
            向下选择菜单项，并更新显示。

        select_up(self) -> None:
            向上选择菜单项，并更新显示。

        select_current(self) -> None:
            选中当前菜单项并进入子菜单。

        select_back(self) -> None:
            返回上级菜单。

        show_message(self, message: str) -> None:
            显示提示消息，中心对齐并带有外部矩形框。

        get_current_menu_name(self) -> Union[str, None]:
            获取当前选中菜单项的名称。
    """

    def __init__(self, oled, name: str, pos_x: int, pos_y: int, width: int, height: int) -> None:
        """
        初始化SimpleOLEDMenu实例。

        Args:
            oled (OLED): OLED显示对象。
            name (str): 菜单名称。
            pos_x (int): 菜单起始X坐标。
            pos_y (int): 菜单起始Y坐标。
            width (int): 菜单宽度。
            height (int): 菜单高度。

        Returns:
            None
        """
        # 初始化OLED显示对象
        self.oled = oled
        # 设置菜单名称
        self.name = name
        # 设置菜单起始X坐标
        self.x = pos_x
        # 设置菜单起始Y坐标
        self.y = pos_y
        # 设置菜单宽度
        self.width = width
        # 设置菜单高度
        self.height = height
        # 创建根菜单节点
        self.head = MenuNode(name)
        # 当前选中的菜单索引，初始为0
        self.selected_index = 0
        # 菜单层级记录栈，用于管理菜单层次
        self.menu_stack = []
        # 当前滚动偏移量，初始化为0
        self.scroll_offset = 0

    def add_menu(self, name: str, parent_name: str = None, enter_callback=None, exit_callback=None) -> None:
        """
        添加新的菜单项。

        Args:
            name (str): 菜单项名称。
            parent_name (str, optional): 父菜单名称，默认值为None，表示添加到根菜单。
            enter_callback (callable, optional): 进入菜单时调用的回调函数。
            exit_callback (callable, optional): 退出菜单时调用的回调函数。

        Returns:
            None

        Raises:
            ValueError: 如果菜单名称过长或父菜单未找到。
        """
        # 检查目录名称是否超出显示范围
        if len(name) * 8 > self.width:
            # 抛出错误
            raise ValueError("Directory name is too long")

        # 检查是否存在重复名称
        if self._find_node(self.head, name):
            # 抛出错误
            raise ValueError("Menu name already exists")

        # 创建新目录节点
        new_node = MenuNode(name, enter_callback, exit_callback)

        # 如果没有父节点，添加到根菜单
        if parent_name is None:
            # 添加到根菜单
            self.head.sub_menu.append(new_node)
        else:
            # 查找父节点并将新菜单节点添加为子菜单
            parent_node = self._find_node(self.head, parent_name)
            if parent_node:
                # 添加子菜单
                parent_node.sub_menu.append(new_node)
            # 若父节点没有找到，抛出错误
            else:
                # 抛出错误
                raise ValueError("Parent menu not found, please check the name")

    def _find_node(self, current, name: str) -> "MenuNode":
        """
        递归查找菜单节点。

        Args:
            current (MenuNode): 当前节点。
            name (str): 要查找的菜单名称。

        Returns:
            MenuNode: 找到的菜单节点，如果没有找到返回None。
        """
        # 如果当前节点为空，返回 None
        if current is None:
            return None

        # 如果当前节点名称匹配，返回当前节点
        if current.name == name:
            return current

        # 遍历当前节点的子菜单
        for sub in current.sub_menu:
            # 递归查找子菜单
            found = self._find_node(sub, name)
            if found:
                # 找到节点，返回
                return found

        # 未找到节点，返回 None
        return None

    def delete_menu(self, name: str) -> None:
        """
        删除指定名称的菜单项。

        Args:
            name (str): 菜单项名称。

        Returns:
            None

        Raises:
            ValueError: 如果菜单项不存在。
        """
        # 从根菜单中删除指定名称的菜单
        self.head.sub_menu = [node for node in self.head.sub_menu if node.name != name]

        # 判断当前子菜单中是不是所有菜单项都被删除
        if len(self.head.sub_menu) == 0:
            # 退出到上一级菜单
            self.select_back()

        # 更新显示
        self.display_menu()

    def display_menu(self) -> None:
        """
        显示当前菜单。

        Args:
            None

        Returns:
            None
        """

        # 清空OLED显示屏
        self.oled.fill(0)
        # 初始化Y轴偏移量
        y_offset = self.y

        # 遍历并显示当前菜单项
        for index, item in enumerate(self.head.sub_menu):
            # 如果当前菜单项是选中状态
            if index == self.selected_index:
                # 反色显示选中项
                self.oled.fill_rect(self.x, y_offset, self.width, 8, 1)
                # 设置选中项字体颜色为黑色
                self.oled.text(item.name, self.x, y_offset, 0)
            else:
                # 设置未选中项字体颜色为白色
                self.oled.text(item.name, self.x, y_offset, 1)

            # 更新Y轴偏移量，考虑滚动偏移
            y_offset += 8

        # 如果子菜单项超过屏幕显示高度，显示滚动偏移
        if len(self.head.sub_menu) > self.height // 8:
            # 清除之前的菜单区域
            self.oled.fill_rect(self.x, self.y, self.width, self.height, 0)
            # 计算可显示的菜单数量
            max_display = min(len(self.head.sub_menu) - self.scroll_offset, self.height // 8)
            # 显示可见的菜单项
            for i in range(max_display):
                # 绘制可视范围内的菜单项
                if i + self.scroll_offset == self.selected_index:
                    # 反色显示选中项
                    self.oled.fill_rect(self.x, self.y + i * 8, self.width, 8, 1)
                    # 黑色字体
                    self.oled.text(self.head.sub_menu[i + self.scroll_offset].name, self.x, self.y + i * 8, 0)
                else:
                    # 白色字体
                    self.oled.text(self.head.sub_menu[i + self.scroll_offset].name, self.x, self.y + i * 8, 1)

        # 更新OLED显示
        self.oled.show()

    def select_down(self) -> None:
        """
        向下选择菜单项。

        Args:
            None

        Returns:
            None
        """
        # 增加选中索引
        self.selected_index += 1

        # 如果超出菜单范围，则重置为0
        if self.selected_index >= len(self.head.sub_menu):
            self.selected_index = 0
            # 重置滚动偏移，显示第一页内容
            self.scroll_offset = 0

        # 滚动显示，如果选中项超出可视范围
        if self.selected_index - self.scroll_offset >= self.height // 8:
            # 滚动下移
            self.scroll_offset += 1

        # 更新显示
        self.display_menu()

    def select_up(self) -> None:
        """
        向上选择菜单项。

        Args:
            None

        Returns:
            None
        """
        # 减少选中索引
        self.selected_index -= 1

        # 如果小于0，则重置为最后一项
        if self.selected_index < 0:
            self.selected_index = len(self.head.sub_menu) - 1
            # 滚动到最后一页
            self.scroll_offset = max(0, len(self.head.sub_menu) - (self.height // 8))
        # 滚动显示，如果选中项小于可视范围的最上方
        elif self.selected_index < self.scroll_offset:
            # 滚动上移
            self.scroll_offset -= 1

        # 更新显示
        self.display_menu()

    def select_current(self) -> None:
        """
        选中当前菜单项并进入子菜单。

        Args:
            None

        Returns:
            None
        """
        # 获取当前选中的菜单
        current_menu = self.head.sub_menu[self.selected_index] if self.selected_index < len(self.head.sub_menu) else None

        # 如果当前菜单存在
        if current_menu:
            # 调用进入回调
            if current_menu.enter_callback:
                current_menu.enter_callback()

            # 如果当前菜单有子菜单，则进入子菜单
            if current_menu.sub_menu:
                # 压入当前菜单到栈中
                self.menu_stack.append(self.head)
                # 更新当前菜单为子菜单
                self.head = current_menu
                # 重置选中索引
                self.selected_index = 0
                # 重置滚动偏移
                self.scroll_offset = 0
                # 更新显示
                self.display_menu()

    def select_back(self) -> None:
        """
        返回上级菜单。

        Args:
            None

        Returns:
            None
        """
        # 如果菜单栈非空
        if self.menu_stack:
            # 调用退出回调
            if self.head.exit_callback:
                self.head.exit_callback()
            # 弹出上级菜单
            self.head = self.menu_stack.pop()
            # 调用进入回调
            if self.head.enter_callback:
                self.head.enter_callback()
            # 重置选中索引
            self.selected_index = 0
            # 更新显示
            self.display_menu()

    def show_message(self, message: str) -> None:
        """
        显示提示消息。

        Args:
            message (str): 要显示的提示消息。

        Returns:
            None

        Raises:
            Exception: 如果消息长度超过13个字符。
        """
        # 检查消息长度，如果过长则抛出异常
        if len(message) > 13:
            raise Exception("Message too long")

        # 获取 OLED 显示的宽度和高度
        oled_width = self.oled.width
        oled_height = self.oled.height

        # 矩形参数
        rect_width = 120
        rect_height = 32
        x = (oled_width - rect_width) // 2
        y = (oled_height - rect_height) // 2

        # 清空显示
        self.oled.fill(0)

        # 先显示原有目录
        self.display_menu()

        # 绘制外部矩形
        self.oled.rect(x, y, rect_width, rect_height, 1)
        # 填充内部矩形
        self.oled.fill_rect(x + 5, y + 5, rect_width - 10, rect_height - 10, 1)

        # 显示提示消息
        message_x = int(x + (rect_width - len(message) * 8) // 2)
        message_y = int(y + (rect_height - 8) // 2)
        self.oled.text(message, message_x, message_y, 0)

        # 刷新显示
        self.oled.show()

        # 等待 1 秒
        time.sleep(1)

        # 清除消息并重新显示原有目录
        self.oled.fill(0)
        self.display_menu()

    def get_current_menu_name(self) -> str:
        """
        获取当前选中的菜单名称。

        Args:
            None

        Returns:
            str: 当前菜单名称，如果没有选中菜单返回None。
        """
        # 获取当前选中的菜单
        current_menu = self.head.sub_menu[self.selected_index] if self.selected_index < len(self.head.sub_menu) else None

        # 如果当前菜单存在，返回菜单名称
        return current_menu.name if current_menu else None


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
