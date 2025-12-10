# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/08/19 12:30
# @Author  : 零高幸
# @File    : piranha_led.py
# @Description : 控制共阳极或共阴极LED的驱动模块
# @License : CC BY-NC 4.0

__version__ = "1.0.0"
__author__ = "零高幸"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23+"

# ======================================== 导入相关模块 =========================================

# 导入硬件相关模块
from machine import Pin
# 导入MicroPython相关模块
from micropython import const

# ======================================== 全局变量 ============================================

# LED 极性常量
# 共阴极：高电平亮
POLARITY_CATHODE = const(0)
# 共阳极：低电平亮
POLARITY_ANODE   = const(1)

# ======================================== 功能函数 ============================================

def _calculate_output(desired_on: bool, polarity: int) -> int:
    """
    根据LED类型和期望状态，计算GPIO应输出的电平。

    Args:
        desired_on (bool): True表示希望LED点亮。
        polarity (int): LED类型，POLARITY_CATHODE 或 POLARITY_ANODE。

    Returns:
        int: 0表示LOW，1表示HIGH。

    Raises:
        ValueError: 如果polarity非法。

    ==========================================
    Calculate GPIO level based on LED type and desired state.

    Args:
        desired_on (bool): True if LED should be on.
        polarity (int): LED type, POLARITY_CATHODE or POLARITY_ANODE.

    Returns:
        int: 0 for LOW, 1 for HIGH.

    Raises:
        ValueError: If polarity is invalid.
    """
    if polarity == POLARITY_CATHODE:
        return 1 if desired_on else 0
    elif polarity == POLARITY_ANODE:
        return 0 if desired_on else 1
    else:
        raise ValueError(f"Invalid polarity: {polarity}")

# ======================================== 自定义类 ============================================

class PiranhaLED:
    """
    控制单个LED的类，支持共阳极和共阴极连接方式。

    遵循：
        - 单一职责：仅控制LED
        - 显式依赖注入：Pin对象由外部传入（或通过引脚号创建）
        - 最小副作用：构造函数不执行长时间操作
        - 可测试性：逻辑与I/O分离
        - 异常策略清晰

    ==========================================
    LED control class supporting common anode and common cathode.
    Follows best practices in design and error handling.
    """

    def __init__(self, pin_number: int, polarity: int = POLARITY_CATHODE):
        """
        初始化LED对象。

        Args:
            pin_number (int): GPIO引脚编号。
            polarity (int): LED类型，POLARITY_CATHODE（默认）或 POLARITY_ANODE。

        Raises:
            ValueError: 如果polarity参数无效。

        Note：
            - 不会立即与硬件通信
            - 构造函数不阻塞

        ==========================================
        Initialize LED object.

        Args:
            pin_number (int): GPIO pin number.
            polarity (int): LED type, POLARITY_CATHODE (default) or POLARITY_ANODE.

        Raises:
            ValueError: If polarity is invalid.

        Note:
            - No hardware communication on init
            - Constructor is non-blocking
        """
        # 参数校验，判断极性是否合法
        if polarity not in (POLARITY_CATHODE, POLARITY_ANODE):
            raise ValueError(f"Invalid polarity: {polarity}")

        # 参数校验，判断引脚号是否合法
        if pin_number < 0:
            raise ValueError(f"Invalid pin number: {pin_number}")

        self._pin = Pin(pin_number, Pin.OUT)
        self._polarity = polarity

    def on(self) -> None:
        """
        点亮LED。

        Raises:
            RuntimeError: 如果GPIO写入失败。

        ==========================================
        Turn on the LED.

        Raises:
            RuntimeError: If GPIO write fails.
        """
        try:
            level = _calculate_output(True, self._polarity)
            self._pin.value(level)
        except Exception as e:
            raise RuntimeError(f"Failed to turn LED on: {e}")

    def off(self) -> None:
        """
        熄灭LED。

        Raises:
            RuntimeError: 如果GPIO写入失败。

        ==========================================
        Turn off the LED.

        Raises:
            RuntimeError: If GPIO write fails.
        """
        try:
            level = _calculate_output(False, self._polarity)
            self._pin.value(level)
        except Exception as e:
            raise RuntimeError(f"Failed to turn LED off: {e}")

    def toggle(self) -> None:
        """
        翻转LED当前状态。

        Raises:
            RuntimeError: 如果GPIO操作失败。

        ==========================================
        Toggle the current state of the LED.

        Raises:
            RuntimeError: If GPIO operation fails.
        """
        try:
            self._pin.value(not self._pin.value())
        except Exception as e:
            raise RuntimeError(f"Failed to toggle LED: {e}")

    def is_on(self) -> bool:
        """
        查询LED是否处于点亮状态（基于本地状态，非真实电平）。

        Returns:
            bool: True表示点亮。

        ==========================================
        Query if LED is on (based on last known state).

        Returns:
            bool: True if on.
        """
        current_level = self._pin.value()
        return current_level == _calculate_output(True, self._polarity)

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
