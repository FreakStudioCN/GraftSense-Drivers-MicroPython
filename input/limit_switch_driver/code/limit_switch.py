# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/25 上午10:35
# @Author  : 缪贵成
# @File    : limit_switch.py
# @Description : 限位开关驱动文件
# @License : MIT

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import micropython
import time
from machine import Pin, Timer

# ======================================== 全局变量 =============================================

# ======================================== 功能函数 =============================================

# ======================================== 自定义类 =============================================

class LimitSwitch:
    """
    限位开关驱动类，支持数字输入检测、消抖和用户回调绑定。

    Attributes:
        _pin (Pin): 绑定的数字引脚对象。
        _callback (callable): 用户回调函数，状态变化时触发。
        _debounce_ms (int): 消抖时间，单位毫秒。
        _timer (Timer): 内部定时器，用于消抖。
        _last_state (int): 上一次读取的开关状态。

    Methods:
        __init__(self, pin: int, callback: callable = None, debounce_ms: int = 50):
            初始化限位开关对象。
        read(self) -> bool:
            读取当前开关状态。
        set_callback(self, callback: callable):
            设置用户回调函数。
        enable(self):
            启用定时器消抖检测。
        disable(self):
            禁用定时器消抖。
        _debounce_handler(self, timer: Timer):
            内部方法，定时器触发的消抖处理函数。
        _scheduled_callback(self, state: int):
            内部方法，通过 micropython.schedule 调度用户回调。
        digital (property):
            返回绑定的数字引脚对象。

    Notes:
        用户回调函数会接收一个 bool 参数：
        True = released（未触发）
        False = pressed（已触发）

    ==========================================

    Limit switch driver class with debounce and user callback support.

    Attributes:
        _pin (Pin): Digital pin object.
        _callback (callable): User callback triggered on state change.
        _debounce_ms (int): Debounce time in ms.
        _timer (Timer): Internal timer for debounce.
        _last_state (int): Last read switch state.

    Methods:
        __init__(self, pin: int, callback: callable = None, debounce_ms: int = 50):
            Initialize limit switch object.
        read(self) -> bool:
            Read current switch state.
        set_callback(self, callback: callable):
            Set user callback function.
        enable(self):
            Enable timer-based debounce detection.
        disable(self):
            Disable debounce timer.
        _debounce_handler(self, timer: Timer):
            Internal method, called by timer for debouncing.
        _scheduled_callback(self, state: int):
            Internal method, schedules user callback via micropython.schedule.
        digital (property):
            Return the digital pin object.

    Notes:
        User callback receives a boolean argument:
        True = released (open), False = pressed (closed)
    """

    def __init__(self, pin: int, callback: callable = None, debounce_ms: int = 50):
        """
        初始化限位开关对象。

        Args:
            pin (int): GPIO 引脚编号。
            callback (callable, optional): 用户回调函数。
            debounce_ms (int, optional): 消抖时间，毫秒，默认 50。

        Notes:
            回调函数会在消抖完成后通过 micropython.schedule 调用。
        ==========================================

        Initialize limit switch object.

        Args:
            pin (int): GPIO pin number.
            callback (callable, optional): User callback function.
            debounce_ms (int, optional): Debounce time in ms, default 50.

        Notes:
            Callback will be called after debounce using micropython.schedule.
        """
        self._pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self._callback = callback
        self._debounce_ms = debounce_ms
        self._timer = Timer(-1)
        self._last_state = self._pin.value()

    def read(self) -> bool:
        """
        读取当前开关状态。

        Returns:
            bool: True = released（未触发），False = pressed（已触发）。

        ==========================================
        Read current switch state.

        Returns:
            bool: True = released (open), False = pressed (closed)
        """
        return bool(self._pin.value())

    def set_callback(self, callback: callable):
        """

        设置用户回调函数。

        Args:
            callback (callable): 用户回调函数。

        Notes:
            - 回调函数会接收一个布尔参数表示开关状态。
        ==========================================

        Set user callback function.

        Args:
            callback (callable): User callback function.

        Notes:
            Callback receives one boolean argument indicating switch state.
        """
        self._callback = callback

    def enable(self):
        """
        启用定时器消抖检测。

        Notes:
            定时器周期为 debounce_ms 毫秒。

        ==========================================

        Enable timer-based debounce detection.

        Notes:
            Timer interval is debounce_ms milliseconds.
        """
        self._timer.init(period=self._debounce_ms, mode=Timer.PERIODIC, callback=self._debounce_handler)

    def disable(self):
        """
        禁用定时器消抖检测。

        ==========================================

        Disable timer-based debounce detection.

        """
        self._timer.deinit()

    def _debounce_handler(self, timer: Timer):
        """

        内部方法：定时器消抖处理函数。
        检查开关状态变化，如果变化则调度用户回调。

        Args:
            timer (Timer): 调度该函数的 Timer 对象。

        Notes:
            使用 micropython.schedule 调度回调。
            True = released, False = pressed

        ==========================================
        Internal method: Timer debounce handler.

        Checks switch state and schedules user callback if changed.

        Args:
            timer (Timer): Timer object triggering this function.

        Notes:
            Uses micropython.schedule to safely run user callback.
            True = released, False = pressed
        """
        state = self._pin.value()
        if state != self._last_state:
            self._last_state = state
            if self._callback:
                micropython.schedule(self._scheduled_callback, state)

    def _scheduled_callback(self, state: int):
        """
        内部方法：通过 micropython.schedule 调度用户回调。

        Args:
            state (int): 引脚状态值（0 或 1）。

        Notes:
            将 state 转换为 bool 传入用户回调。
            True = released, False = pressed

        ==========================================

        Internal method: Schedule user callback via micropython.schedule.

        Args:
            state (int): Pin level (0 or 1).

        Notes:
            Converts state to bool before passing to callback.
            True = released, False = pressed
        """
        self._callback(bool(state))

    @property
    def digital(self) -> Pin:
        """
        返回绑定的数字引脚对象。

        Returns:
            Pin: 数字引脚对象

        ==========================================

        Return the digital pin object.

        Returns:
            Pin: Digital pin object
        """
        return self._pin

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ==============================================
