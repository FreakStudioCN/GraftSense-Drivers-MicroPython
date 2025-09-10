# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/04 10:21
# @Author  : 侯钧瀚
# @File    : led_bar.py
# @Description : 基于 PCF8574 的 8 段光条数码管驱动（仅一个 LEDBar 类）
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : CCBYNC
__version__ = "0.1.0"
__author__ = "侯钧瀚"
__license__ = "CCBYNC"
__platform__ = "MicroPython v1.19+"

# ======================================== 自定义类 ============================================
class LEDBar:
    """
    基于 PCF8574 的 8 段光条数码管控制类（仅此一个类，对外提供 5 个方法）。
    - 约定：传入的 pcf8574 对象实现 write(value:int) 方法，将 8 位端口值写入芯片。
    - 默认按低电平点亮（active-low），即逻辑 1=点亮，将被转换为物理 0 输出。
    - 索引从 0 到 7，约定 0 对应 P0，7 对应 P7。

    对外方法：
      1) __init__(self, pcf8574)        —— 传入 PCF8574 实例
      2) set_led(self, index:int, value:bool) —— 点亮/熄灭单个 LED（0~7）
      3) set_all(self, value:int)       —— 设置 8 位图样（bit1=亮）
      4) display_level(self, level:int) —— 点亮前 N 个（0~8）
      5) clear(self)                    —— 全部熄灭
    ==============
    8-segment LED bar controller using a PCF8574 backend (single class, 5 public methods).
    - Contract: the provided `pcf8574` object must implement `write(value:int)` to output an
      8-bit port value to the chip.
    - Assumes active-low hardware: logical 1 (ON) is converted to physical 0 on the port.
    - Indices 0..7 map to P0..P7 respectively.

    Public methods:
      1) __init__(self, pcf8574)              — accept a PCF8574-like instance
      2) set_led(self, index:int, value:bool) — turn one LED (0..7) on/off
      3) set_all(self, value:int)             — set 8-bit pattern (bit1=ON)
      4) display_level(self, level:int)       — light the first N LEDs (0..8)
      5) clear(self)                          — turn all LEDs off
    """

    NUM_LEDS = 8          # LED 数量
    _ACTIVE_LOW = True    # 常见硬件为低电平点亮

    def __init__(self, pcf8574):
        """
        构造函数，传入 PCF8574 实例（需实现 write(value:int)）。
        - 内部维护“逻辑状态” self._state，约定 bit1=点亮。
        - 上电默认全灭（逻辑 0）。

        参数:
            pcf8574: 提供 write(value:int) 方法的对象。

        异常:
            ValueError: 若未提供 write 方法。
            RuntimeError: 底层写失败。
        ==============
        Constructor. Expects a PCF8574-like object with `write(value:int)`.
        - Maintains a logical state `self._state` where bit=1 means LED ON.
        - Powers up with all OFF (logical 0).

        Args:
            pcf8574: object providing `write(value:int)`.

        Raises:
            ValueError: if no compatible `write` method is found.
            RuntimeError: if low-level write fails.
        """
        if not hasattr(pcf8574, "write"):
            raise ValueError("pcf8574 must provide write(value:int)")
        self._pcf = pcf8574
        self._state = 0
        self._flush()

    def set_led(self, index: int, value: bool):
        """
        点亮或熄灭指定 LED（0~7），并立即写入硬件。
        - value=True 表示点亮；False 表示熄灭。
        - 超界索引将抛出 ValueError。

        参数:
            index (int): 0..7
            value (bool): True=点亮，False=熄灭
        ==============
        Turn one LED (0..7) ON/OFF and flush to hardware.
        - `value=True` turns it ON; `False` turns it OFF.
        - Raises ValueError if index is out of range.

        Args:
            index (int): 0..7
            value (bool): True=ON, False=OFF
        """
        self._ensure_index(index)
        if value:
            self._state |= (1 << index)
        else:
            self._state &= ~(1 << index)
        self._flush()

    def set_all(self, value: int):
        """
        设置全部 LED 的逻辑状态（bit1=亮），并立即写入硬件。
        - 仅使用低 8 位；超出范围将被裁剪到 0..255。

        参数:
            value (int): 0..255
        ==============
        Set all LEDs with an 8-bit logical pattern (bit1=ON) and flush.
        - Only the lowest 8 bits are used; the value is clipped to 0..255.

        Args:
            value (int): 0..255
        """
        self._state = self._clip8(value)
        self._flush()

    def display_level(self, level: int):
        """
        显示进度：点亮前 N 个 LED（从 index 0 起数）。
        - level=0 全灭；level=8 全亮；其他为掩码 (1<<level)-1。

        参数:
            level (int): 0..8
        ==============
        Display a level by lighting the first N LEDs starting at index 0.
        - level=0: all OFF; level=8: all ON; otherwise mask is (1<<level)-1.

        Args:
            level (int): 0..8
        """
        if not isinstance(level, int) or not (0 <= level <= self.NUM_LEDS):
            raise ValueError("level must be int in 0..8")
        mask = (1 << level) - 1 if level > 0 else 0
        self._state = mask & 0xFF
        self._flush()

    def clear(self):
        """
        熄灭所有 LED（逻辑全 0），并立即写入硬件。
        ==============
        Turn all LEDs OFF (logical 0) and flush to hardware.
        """
        self._state = 0
        self._flush()

    # ------------------------- 内部工具方法 -------------------------
    def _ensure_index(self, index):
        # 校验索引范围 0..7
        if not isinstance(index, int) or not (0 <= index < self.NUM_LEDS):
            raise ValueError("index must be int in 0..7")

    def _clip8(self, value):
        # 将整数裁剪到 0..255
        if not isinstance(value, int):
            raise ValueError("value must be int")
        if value < 0:
            return 0
        if value > 0xFF:
            return 0xFF
        return value

    def _logical_to_port(self, logical_byte):
        # 逻辑（1=亮）到物理端口值转换；默认低电平点亮
        b = logical_byte & 0xFF
        return (~b) & 0xFF if self._ACTIVE_LOW else b

    def _flush(self):
        # 将当前逻辑状态刷新到 PCF8574
        try:
            self._pcf.write(self._logical_to_port(self._state))
        except Exception as e:
            raise RuntimeError("PCF8574 write failed") from e
