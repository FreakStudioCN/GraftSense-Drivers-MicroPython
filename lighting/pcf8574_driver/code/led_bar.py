# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/08 10:21
# @Author  : 侯钧瀚
# @File    : led_bar.py
# @Description : 基于 PCF8574 的 8 段光条数码管驱动（仅一个 LEDBar 类）
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : CC BY-NC 4.0
__version__ = "0.1.0"
__author__ = "侯钧瀚"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23.0"
# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class LEDBar:
    """
    LEDBar 类，用于通过 PCF8574 芯片控制 8 段 LED 光条数码管，实现单独或批量点亮/熄灭 LED。

    Attributes:
        _pcf: 提供 write(value:int) 方法的 PCF8574 实例。
        _state (int): 当前 8 位 LED 逻辑状态，bit1=点亮。

    Methods:
        __init__(pcf8574) -> None: 初始化 LEDBar，传入 PCF8574 实例。
        set_led(index: int, value: bool) -> None: 点亮或熄灭指定 LED。
        set_all(value: int) -> None: 设置全部 LED 的点亮图样。
        display_level(level: int) -> None: 点亮前 N 个 LED，显示进度。
        clear() -> None: 熄灭所有 LED。
    ==========================================

    LEDBar driver class for controlling an 8-segment LED bar via PCF8574.
    Provides methods for single LED control, batch control, and level display.

    Attributes:
        _pcf: PCF8574 instance providing write(value:int).
        _state (int): Current 8-bit logical LED state, bit1=ON.

    Methods:
        __init__(pcf8574) -> None: Initialize LEDBar with a PCF8574 instance.
        set_led(index: int, value: bool) -> None: Turn a specific LED on/off.
        set_all(value: int) -> None: Set all LEDs with an 8-bit pattern.
        display_level(level: int) -> None: Light up the first N LEDs.
        clear() -> None: Turn all LEDs off.
    """

    NUM_LEDS = 8
    _ACTIVE_LOW = True

    def __init__(self, pcf8574):
        """
        初始化 LEDBar 类。

        Args:
            pcf8574: 提供 write(value:int) 方法的 PCF8574 实例。

        Raises:
            ValueError: 如果未提供 write 方法。

        ==========================================

        Initialize LEDBar class.

        Args:
            pcf8574: PCF8574 instance providing write(value:int) method.

        Raises:
            ValueError: If no compatible write method is found.
        """
        if not hasattr(pcf8574, "write"):
            raise ValueError("pcf8574 must provide write(value:int)")
        self._pcf = pcf8574
        self._state = 0
        self._flush()

    def set_led(self, index: int, value: bool):
        """
        点亮或熄灭指定 LED（0~7），并立即写入硬件。

        Args:
            index (int): 0..7
            value (bool): True=点亮，False=熄灭

        ==========================================

        Turn one LED (0..7) ON/OFF and flush to hardware.

        Args:
            index (int): 0..7
            value (bool): True=ON, False=OFF

        """
        self._ensure_index(index)
        self._state = (self._state | (1 << index)) if value else (self._state & ~(1 << index))
        self._flush()

    def set_all(self, value: int):
        """
        设置全部 LED 的逻辑状态（bit1=亮），并立即写入硬件。

        Args:
            value (int): 0..255

        ==========================================

        Set all LEDs with an 8-bit logical pattern (bit1=ON) and flush.

        Args:
            value (int): 0..255
        """
        self._state = self._clip8(value)
        self._flush()

    def display_level(self, level: int):
        """
        显示进度：点亮前 N 个 LED（从 index 0 起数）。

        Args:
            level (int): 0..8

        Raises:
            ValueError: level 越界

        ==========================================

        Display a level by lighting the first N LEDs starting at index 0.

        Args:
            level (int): 0..8

        Raises:
            ValueError: If level is out of range.
        """
        if not isinstance(level, int) or not (0 <= level <= self.NUM_LEDS):
            raise ValueError("level must be int in 0..8")
        self._state = ((1 << level) - 1) & 0xFF if level > 0 else 0
        self._flush()

    def clear(self):
        """
        熄灭所有 LED（逻辑全 0），并立即写入硬件。

        ==========================================

        Turn all LEDs OFF (logical 0) and flush to hardware.
        """
        self._state = 0
        self._flush()

    def _ensure_index(self, index):
        """
        校验 LED 索引是否在有效范围 0..7。

        Args:
            index (int): LED 索引，必须为 0..7 的整数。

        Raises:
            ValueError: 如果 index 不是整数或超出范围。

        ==========================================

        Ensure the LED index is within valid range 0..7.

        Args:
            index (int): LED index, must be integer in 0..7.

        Raises:
            ValueError: If index is not int or out of range.
        """
        if not isinstance(index, int) or not (0 <= index < self.NUM_LEDS):
            raise ValueError("index must be int in 0..7")

    def _clip8(self, value):
        """
        将输入整数裁剪到 0..255 范围。

        Args:
            value (int): 输入值。

        Returns:
            int: 裁剪后的 0..255 整数。

        Raises:
            ValueError: 如果 value 不是整数。

        ==========================================

        Clip input integer to 0..255.

        Args:
            value (int): Input value.

        Returns:
            int: Clipped value in 0..255.

        Raises:
            ValueError: If value is not int.
        """
        if not isinstance(value, int):
            raise ValueError("value must be int")
        return max(0, min(0xFF, value))

    def _logical_to_port(self, logical_byte):
        """
        将逻辑 LED 状态（1=亮）转换为 PCF8574 端口值。默认低电平点亮。

        Args:
            logical_byte (int): 8 位逻辑 LED 状态。

        Returns:
            int: 端口输出值。

        ==========================================

        Convert logical LED state (1=ON) to PCF8574 port value.
        Active-low by default.

        Args:
            logical_byte (int): 8-bit logical LED state.

        Returns:
            int: Port output value.
        """
        b = logical_byte & 0xFF
        return (~b) & 0xFF if self._ACTIVE_LOW else b

    def _flush(self):
        """
        将当前 LED 状态刷新写入 PCF8574 芯片。

        Raises:
            RuntimeError: 写入 PCF8574 失败。

        ==========================================

        Flush current LED state to PCF8574 chip.

        Raises:
            RuntimeError: If write to PCF8574 fails.
        """
        try:
            self._pcf.write(self._logical_to_port(self._state))
        except Exception as e:
            raise RuntimeError("PCF8574 write failed") from e

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================