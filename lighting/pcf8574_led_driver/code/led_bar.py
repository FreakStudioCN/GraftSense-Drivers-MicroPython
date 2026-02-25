# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/08 10:21
# @Author  : 侯钧瀚
# @File    : led_bar.py
# @Description : 基于 PCF8574 的 8 段光条数码管驱动（仅一个 LEDBar 类）
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : MIT

__version__ = "0.1.0"
__author__ = "侯钧瀚"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

from pcf8574 import PCF8574

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class LEDBar:
    """
    基于 PCF8574 的 8 位 LED 灯条驱动类。
    提供单个/多个 LED 控制、全局清除，以及电平显示（点亮前 N 个 LED）功能。
    常用于电平指示、进度显示和调试输出。

    Attributes:
        pcf (PCF8574): 已初始化好的 PCF8574 实例，用于控制 I/O 扩展口。

    Methods:
        __init__(pcf8574: PCF8574):
            初始化 LEDBar 并清空所有 LED。
        set_led(index: int, value: bool) -> None:
            点亮或熄灭指定 LED。
        set_all(value: int) -> None:
            设置所有 LED 的状态（8 位二进制数）。
        display_level(level: int) -> None:
            根据 level 值点亮前 N 个 LED。
        clear() -> None:
            熄灭所有 LED。

    Notes:
        - 需要依赖 PCF8574 I/O 扩展芯片，需通过 I2C 初始化。
        - 操作非中断安全（I2C 驱动限制），不建议在 ISR 中直接调用。

    ==========================================

    8-bit LED bar driver based on PCF8574.
    Provides per-LED control, batch update, and level display (light up first N LEDs).
    Commonly used for level indicators, progress display, and debugging.

    Attributes:
        pcf (PCF8574): Pre-initialized PCF8574 instance for controlling I/O expander.

    Methods:
        __init__(pcf8574: PCF8574):
            Initialize LEDBar and clear all LEDs.
        set_led(index: int, value: bool) -> None:
            Turn ON/OFF a specific LED.
        set_all(value: int) -> None:
            Set all LEDs at once (8-bit binary).
        display_level(level: int) -> None:
            Light up the first N LEDs based on level.
        clear() -> None:
            Turn off all LEDs.

    Notes:
        - Requires PCF8574 I/O expander initialized via I2C.
        - Not ISR-safe due to I2C driver limitations.
    """

    def __init__(self, pcf8574: "PCF8574") -> None:
        """
        基于 PCF8574 的 8 位 LED 灯条驱动类。

        Args:
            pcf8574 (PCF8574): 已初始化好的 PCF8574 实例或实现了兼容方法的对象。

        Raises:
            TypeError:
                - 如果传入对象未实现 `check`、`port`、`pin` 或 `toggle` 方法。

        Notes:
            默认初始化时会清空所有 LED 状态。

        ==========================================

        8-bit LED bar driver based on PCF8574.

        Args:
            pcf8574 (PCF8574): Pre-initialized PCF8574 instance
                               or any object implementing the required methods.

        Raises:
            TypeError:
                - If the provided object does not implement
                  `check`, `pin`, or `toggle` methods.

        Notes:
            All LEDs will be cleared on initialization.
        """
        required_methods = ["check", "pin", "toggle"]
        for method in required_methods:
            if not hasattr(pcf8574, method) or not callable(getattr(pcf8574, method)):
                raise TypeError(f"pcf8574 must implement method: {method}")
        self.pcf = pcf8574
        self.clear()

    def set_led(self, index: int, value: bool) -> None:
        """
        点亮或熄灭指定 LED。

        Args:
            index (int): LED 索引 0~7。
            value (bool): True=点亮, False=熄灭。

        Raises:
            ValueError: 当 index 不在 0~7 范围内时抛出。

        ==========================================

        Turn on/off a specific LED.

        Args:
            index (int): LED index, range 0–7.
            value (bool): True=ON, False=OFF.

        Raises:
            ValueError: If index is out of 0–7.
        """
        if not 0 <= index <= 7:
            raise ValueError("LED index must be 0~7")
        self.pcf.pin(index, 1 if value else 0)

    def set_all(self, value: int) -> None:
        """
        设置所有 LED 的状态。

        Args:
            value (int): 8 位二进制数，每一位对应一个 LED。
                         例如 0b11110000 表示点亮前 4 个 LED。

        Raises:
            ValueError: 如果 value 不在 0~255 范围内。

        ==========================================

        Set the state of all LEDs.

        Args:
            value (int): 8-bit value, each bit maps to one LED.
                         For example, 0b11110000 lights the first 4 LEDs.

        Raises:
            ValueError: If value is not in the range 0–255.
        """
        if not 0 <= value <= 0xFF:
            raise ValueError("value must be between 0 and 255 (0x00–0xFF)")

        self.pcf.port = value & 0xFF

    def display_level(self, level: int) -> None:
        """
        根据传入值点亮前 N 个 LED。

        Args:
            level (int): 范围 0~8，点亮前 N 个 LED。

        Raises:
            ValueError: 当 level 不在 0~8 范围内时抛出。

        ==========================================

        Light up the first N LEDs.

        Args:
            level (int): Range 0–8, lights the first N LEDs.

        Raises:
            ValueError: If level is out of 0–8.
        """
        if not 0 <= level <= 8:
            raise ValueError("Level must be 0~8")

        value = (1 << level) - 1 if level > 0 else 0
        self.set_all(value)

    def clear(self) -> None:
        """
        熄灭所有 LED。

        ==========================================

        Turn off all LEDs.
        """
        self.set_all(0x00)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
