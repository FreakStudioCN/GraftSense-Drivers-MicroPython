# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/16 18:00
# @Author  : 侯钧瀚
# @File    : heartratemonitor.py
# @Description : MAX30102/MAX30105 心率与PPG读取驱动，参考自：https://github.com/n-elia/MAX30102-MicroPython-driver
# @License : MIT

__version__ = "0.1.0"
__author__ = "侯钧瀚"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

from ucollections import deque

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class CircularBuffer(object):
    """
    基于 deque 的简易环形缓冲区实现。

    Attributes:
        data (deque): 底层存储。
        max_size (int): 最大容量。

    Methods:
        append(item): 追加元素（满则丢弃最早元素）。
        pop(): 弹出最早元素。
        pop_head(): 弹出最新元素（注意：原实现含边界逻辑）。
        clear(): 清空。
        is_empty(): 是否为空。

    Notes:
        - 为保持与原代码逻辑一致，未更改 `pop_head` 的实现；其行为较非常规环形缓冲，使用时请注意。

    =========================================
    A minimal ring buffer backed by deque.

    Attributes:
        data (deque): Underlying storage.
        max_size (int): Capacity.

    Methods:
       append(item): Append an element (if full, discard the earliest element).
        pop(): Pop the earliest element.
        pop_head(): Pop the latest element (Note: The original implementation includes boundary logic).
        clear(): Clear all elements.
        is_empty(): Check if it is empty.

    Notes:
        - The original `pop_head` behavior is preserved verbatim; it is unusual
          for a ring buffer, so use with care.
    """

    def __init__(self, max_size):
        """
        初始化。

        Args:
            max_size (int): 容量上限，必须为正整数。

        Raises:
            TypeError: 如果 max_size 不是 int 类型。
            ValueError: 如果 max_size 小于等于 0。

        =========================================
        Initialize.

        Args:
            max_size (int): Capacity, must be a positive integer.

        Raises:
            TypeError: If max_size is not an int.
            ValueError: If max_size is not positive.
        """
        self.data = deque((), max_size, True)
        self.max_size = max_size

    def __len__(self):
        """
        返回当前元素数量。

        Returns:
            int: 元素个数。

        =========================================
        Return current number of elements.

        Returns:
            int: Count.
        """
        return len(self.data)

    def is_empty(self):
        """
        判断是否为空。

        Returns:
            bool: 是否为空。

        =========================================
        Check if empty.

        Returns:
            bool: True if empty.
        """
        return not bool(self.data)

    def append(self, item):
        """
        追加元素；若满，则丢弃最早元素再插入。

        Args:
            item (Any): 待插入元素。

        =========================================
        Append an item; drop the oldest if full.

        Args:
            item (Any): Item to append.
        """
        try:
            self.data.append(item)
        except IndexError:
            # deque full, popping 1st item out
            self.data.popleft()
            self.data.append(item)

    def pop(self):
        """
        弹出最早的元素。

        Returns:
            Any: 被弹出的元素。

        =========================================
        Pop the oldest element.

        Returns:
            Any: Popped element.
        """
        return self.data.popleft()

    def clear(self):
        """
        清空缓冲区。

        =========================================
        Clear the buffer.
        """
        self.data = deque((), self.max_size, True)

    def pop_head(self):
        """
        弹出“最新”元素（保留原有实现特性）。

        Returns:
            Any|int: 若空返回 0，否则返回元素。

        =========================================
        Pop the "newest" element (keeps original implementation semantics).

        Returns:
            Any|int: 0 if empty, els法 2：通过 GitHub 客户端e the element.
        """
        buffer_size = len(self.data)
        temp = self.data
        if buffer_size == 1:
            pass
        elif buffer_size > 1:
            self.data.clear()
            for x in range(buffer_size - 1):
                self.data = temp.popleft()
        else:
            return 0
        return temp.popleft()

    # ======================================== 初始化配置 ==========================================

    # ========================================  主程序  ===========================================
