# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/28 上午11:22
# @Author  : ben0i0d
# @File    : processbar.py
# @Description : 进度条驱动代码

__version__ = "0.1.0"
__author__ = "ben0i0d"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class ProgressBar:
    """
    终端进度条类，用于在终端显示一个可更新的进度条。

    Attributes:
        max_value (int): 进度条的最大值，表示任务总进度。
        bar_length (int): 进度条的总长度（宽度），默认为 50。

    Methods:
        __init__(max_value: int, bar_length: int = 50) -> None: 初始化进度条。
        update(current_value: int) -> None: 更新进度条显示，传入当前进度值。
        reset() -> None: 重置进度条为 0%，显示全红。

    Notes:
        当前值小于 0 时会被置为 0，大于 max_value 时会被置为 max_value。
        已完成部分用绿色显示，未完成部分用红色显示。
        进度条在终端使用 `\r` 回车刷新，不会换行。

    ==========================================

    Terminal progress bar class for displaying an updatable progress bar.

    Attributes:
        max_value (int): Maximum value of the progress bar (total progress).
        bar_length (int): Total length (width) of the progress bar. Default is 50.

    Methods:
        __init__(max_value: int, bar_length: int = 50) -> None: Initialize progress bar.
        update(current_value: int) -> None: Update progress bar display with current value.
        reset() -> None: Reset progress bar to 0% (all red).

    Notes:
        Current value < 0 will be clamped to 0, > max_value will be clamped to max_value.
        Completed portion is shown in green, remaining portion in red.
        The progress bar refreshes in-place using `\r` without creating new lines.
    """

    def __init__(self, max_value: int, bar_length: int = 50) -> None:
        """
        初始化进度条。

        Args:
            max_value (int): 进度条的最大值，达到此值时进度条显示 100%。
            bar_length (int): 进度条的总长度（宽度），默认为 50。

        ==========================================

        Initialize the progress bar.

        Args:
            max_value (int): Maximum value of the progress bar, at which it shows 100%.
            bar_length (int): Total length (width) of the progress bar. Default is 50.
        """
        self.max_value = max_value
        self.bar_length = bar_length

    def update(self, current_value: int) -> None:
        """
        更新进度条。

        根据当前值计算并刷新进度条的显示，确保当前值在合法范围内。

        Args:
            current_value (int): 当前进度条的值，自动限制在 [0, max_value] 范围。

        Returns:
            None

        ==========================================

        Update the progress bar.

        Calculate and refresh the progress bar display based on the current value.
        The current value is clamped within [0, max_value].

        Args:
            current_value (int): Current value of the progress bar.

        Returns:
            None
        """
        if current_value > self.max_value:
            current_value = self.max_value
        if current_value < 0:
            current_value = 0

        progress = current_value / self.max_value
        block = int(self.bar_length * progress)

        # 绿色表示进度，红色表示剩余
        bar = '\033[92m' + '█' * block + '\033[91m' + '-' * (self.bar_length - block) + '\033[0m'
        print(f"\r[{bar}]", end='')

    def reset(self) -> None:
        """
        重置进度条。

        将进度条重置为 0%，显示全红色。

        Returns:
            None

        ==========================================

        Reset the progress bar.

        Reset the progress bar to 0% (all red).

        Returns:
            None
        """
        print(f"\r\033[91m[{'-' * self.bar_length}]\033[0m", end='')

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
