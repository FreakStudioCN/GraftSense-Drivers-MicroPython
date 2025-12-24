# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 上午11:42
# @Author  : 缪贵成
# @File    : pcf9685keys.py
# @Description : 五向按键驱动库
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import time
from machine import Timer

# ======================================== 全局变量 ============================================

# debounce time in milliseconds
DEBOUNCE_MS = 20
# 五向按键引脚映射（根据实际接线修改）
KEYS_MAP = {
    'UP': 0,
    'DOWN': 3,
    'LEFT': 1,
    'RIGHT': 2,
    'CENTER': 4,
    'SW1':5,
    'SW2':7,
}

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class PCF8574Keys:
    """
    该类管理基于 PCF8574 I/O 扩展芯片的五向按键模块，提供按键状态读取与回调功能，带定时器消抖。

    Attributes:
        _pcf (object): PCF8574 实例对象。
        _keys (dict): 按键映射字典，例如 {'UP': 4, 'DOWN': 1, 'LEFT': 2, 'RIGHT': 0, 'CENTER': 3}。
        _callback (callable|None): 按键状态变化回调函数。
        _state (dict): 当前按键状态缓存。
        _last_state (dict): 上一次按键状态，用于检测变化。
        _last_time (dict): 上一次状态变化时间，用于消抖。
        _timer (Timer): MicroPython 定时器对象，用于轮询扫描按键。

    Methods:
        read_key(key_name: str) -> bool: 读取指定按键状态。
        read_all() -> dict: 返回所有按键状态。
        deinit() -> None: 释放资源。

    Notes:
        - 定时器轮询会执行 I2C 操作，非 ISR-safe。
        - read_key 和 read_all 方法只读取缓存状态，不会直接访问 I2C。
        - 回调函数可能在定时器中被调用，不要在回调中执行耗时操作。

    ==========================================

    This class manages a five-way button module via PCF8574 I/O expander with timer-based debounce.

    Attributes:
        _pcf (object): PCF8574 instance.
        _keys (dict): Button mapping dictionary, e.g., {'UP': 4, 'DOWN': 1, 'LEFT': 2, 'RIGHT': 0, 'CENTER': 3}.
        _callback (callable|None): Callback function when button state changes.
        _state (dict): Current button state cache.
        _last_state (dict): Previous button state for change detection.
        _last_time (dict): Last state change timestamp for debounce.
        _timer (Timer): MicroPython timer for periodic scanning.

    Methods:
        read_key(key_name: str) -> bool: Read the current state of a specific button.
        read_all() -> dict: Get a dictionary of all button states.
        deinit() -> None: Release resources.

    Notes:
        - Timer-based polling performs I2C reads, not ISR-safe.
        - read_key and read_all only read cached states, not I2C directly.
        - Callback may be invoked in timer context; avoid heavy operations in callback.
    """

    def __init__(self, pcf: object, keys: dict, callback: callable = None):

        """
        初始化五向按键模块对象，并启动定时器进行轮询消抖。

        Args:
            pcf (object): PCF8574 实例对象，必须提供 read(pin) 方法。
            keys (dict): 按键映射字典。
            callback (callable, optional): 按键状态变化回调函数，格式 callback(key_name: str, state: bool)。

        Raises:
            TypeError: 当 pcf 无 read 方法或 callback 非可调用对象。
            ValueError: 当 keys 不是非空字典。

        Notes:
            初始化时会启动定时器进行消抖扫描，非 ISR-safe。

        ==========================================

        Initialize the five-way button module object and start timer-based debounce.

        Args:
            pcf (object): PCF8574 instance with read(pin) method.
            keys (dict): Button mapping dictionary.
            callback (callable, optional): Callback function on state change, format: callback(key_name: str, state: bool).

        Raises:
            TypeError: If pcf has no read method or callback is not callable.
            ValueError: If keys is not a non-empty dictionary.

        Notes:
            Timer-based polling is started internally for debounce, not ISR-safe.
        """

        if not hasattr(pcf, "pin"):
            raise TypeError("pcf parameter must have a read(pin) method")
        if not isinstance(keys, dict) or not keys:
            raise ValueError("keys parameter must be a non-empty dictionary")
        if callback is not None and not callable(callback):
            raise TypeError("callback must be callable")

        self._pcf = pcf
        self._keys = keys
        self._callback = callback
        # debounce state cache
        self._state = {k: False for k in keys.keys()}
        self._last_state = self._state.copy()
        self._last_time = {k: 0 for k in keys.keys()}

        # create timer for periodic scanning
        self._timer = Timer(-1)
        self._timer.init(period=10, mode=Timer.PERIODIC, callback=self._scan_keys)

    def led_on(self):
        self._pcf.port =0b00000000

    def led_off(self):
        self._pcf.port =0b01000000

    def _scan_keys(self, t):
        """
        定时器回调函数，轮询扫描按键状态并处理消抖。

        Args:
            t (Timer): MicroPython 定时器对象。

        Notes:
            执行 I2C 读取，非 ISR-safe。

        ==========================================

        Timer callback for scanning button states and handling debounce.

        Args:
            t (Timer): MicroPython timer object.

        Notes:
            Performs I2C reads, not ISR-safe.
        """
        now = time.ticks_ms()
        for key_name, pin in self._keys.items():
            try:
                # low level means pressed
                raw = not bool(self._pcf.pin(pin))
            except Exception:
                # ignore I2C errors
                continue

            # debounce logic
            if raw != self._state[key_name]:
                if time.ticks_diff(now, self._last_time[key_name]) > DEBOUNCE_MS:
                    self._state[key_name] = raw
                    self._last_time[key_name] = now
                    # trigger callback if state changed
                    if self._callback and raw != self._last_state[key_name]:
                        try:
                            self._callback(key_name, raw)
                        except Exception:
                            pass
            self._last_state[key_name] = self._state[key_name]

    def read_key(self, key_name: str) -> bool:
        """
        读取指定按键当前状态。

        Args:
            key_name (str): 按键名称。

        Returns:
            bool: True 表示按下，False 表示未按下。

        Raises:
            ValueError: 当按键名称未知时。

        Notes:
            返回缓存状态，不执行 I2C 读取。

        ==========================================

        Read the current state of a specific button.

        Args:
            key_name (str): Button name.

        Returns:
            bool: True if pressed, False otherwise.

        Raises:
            ValueError: If button name is unknown.

        Notes:
            Returns cached state, no I2C read performed.
        """
        if key_name not in self._keys:
            raise ValueError(f"Unknown button name: {key_name}")
        return self._state[key_name]

    def read_all(self) -> dict:
        """
        返回所有按键状态字典。

        Returns:
            dict: 所有按键状态。

        Notes:
            返回缓存状态，不执行 I2C 读取。

        ==========================================

        Return a dictionary of all button states.

        Returns:
            dict: All button states.

        Notes:
            Returns cached states, no I2C read performed.
        """
        return self._state.copy()

    def deinit(self):
        """
        停止定时器并释放资源。

        Notes:
            清空内部引用，释放占用的对象。

        ==========================================

        Stop the timer and release resources.

        Notes:
            Clears internal references and frees resources.
        """
        self._timer.deinit()
        self._callback = None
        self._state.clear()
        self._last_state.clear()
        self._last_time.clear()
        self._keys.clear()
        self._pcf = None

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
