# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/25 上午9:48
# @Author  : 缪贵成
# @File    : hall_sensor_oh34n.py.py
# @Description : 霍尔传感器驱动文件（数字）
# @License : MIT

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 ==========================================

import micropython
from machine import Pin

# ======================================== 全局变量 =============================================

# ======================================== 功能函数 =============================================

# ======================================== 自定义类 =============================================

class HallSensorOH34N:
    """
    基于 OH34N 芯片的霍尔传感器驱动类。
    支持磁场检测、回调函数设置和中断触发。
    Attributes:
        _pin (Pin): 绑定的数字输入引脚。
        _callback (callable): 用户定义的回调函数，磁场变化时触发。
        _irq (IRQ): 内部中断对象。

    Methods:
        __init__(pin: int, callback: callable = None) -> None:
            初始化霍尔传感器，绑定数字引脚，可选设置回调函数。
        read() -> bool:
            读取传感器状态，返回是否检测到磁场。
        set_callback(callback: callable) -> None:
            设置磁场变化时的回调函数。
        _irq_handler(pin: Pin) -> None:
            内部 IRQ 中断处理函数，通过 micropython.schedule 调度用户回调。
        _scheduled_callback(arg: int) -> None:
            内部方法，执行用户回调。
        enable() -> None:
            启用霍尔传感器中断检测。
        disable() -> None:
            禁用霍尔传感器中断检测。
        digital (property) -> Pin:
            获取绑定的数字引脚对象。

    Notes:
        传感器输出为数字信号，高电平表示检测到磁场。
        回调函数通过 micropython.schedule 调度，确保中断安全。
        需调用 enable() 才能启用中断检测。
        ISR 内不要执行耗时操作，回调在主线程安全执行。

    ==========================================

    Driver class for OH34N Hall sensor.
    Supports magnetic field detection, callback setup, and interrupt triggering.

    Attributes:
        _pin (Pin): Bound digital input pin.
        _callback (callable): User-defined callback, triggered on magnetic field change.
        _irq (IRQ): Internal interrupt object.

    Methods:
        __init__(pin: int, callback: callable = None) -> None:
            Initialize the Hall sensor, bind digital pin and optional callback.
        read() -> bool:
            Read Hall sensor state.
        set_callback(callback: callable) -> None:
            Set callback function for magnetic field change.
        _irq_handler(pin: Pin) -> None:
            Internal IRQ interrupt handler, schedules user callback.
        _scheduled_callback(arg: int) -> None:
            Internal method, executes user callback.
        enable() -> None:
            Enable Hall sensor interrupt detection.
        disable() -> None:
            Disable Hall sensor interrupt detection.
        digital (property) -> Pin:
            Get the bound digital pin object.
    Notes:
        Sensor outputs digital signal, high level indicates magnetic field detected.
        Callback is scheduled via micropython.schedule to ensure IRQ safety.
        Must call enable() to activate interrupt detection.
        Avoid heavy operations in ISR; callback executes safely in main thread.
    """
    def __init__(self, pin: int, callback: callable = None) -> None:
        """
        初始化霍尔传感器，指定数字引脚并可选绑定回调函数。

        Args:
            pin (int): 传感器 DO 引脚连接的 GPIO 引脚号。
            callback (callable, optional): 用户回调函数，磁场变化时触发。
        Notes:
            默认配置引脚为输入模式。
            若设置回调函数，可通过 enable() 启用中断。

        ==========================================

        Initialize the Hall sensor, bind digital pin and optional callback.

        Args:
            pin (int): GPIO pin number connected to sensor DO pin.
            callback (callable, optional): User callback, triggered on magnetic field change.

        Notes:
            - Pin is configured as input mode by default.
            - If callback is set, call enable() to activate interrupts.
        """
        self._pin = Pin(pin, Pin.IN)
        self._callback = callback
        self._irq = None

    def read(self) -> bool:
        """

        读取霍尔传感器状态。

        Returns:
            bool: True 表示检测到磁场，False 表示未检测到。

        ==========================================

        Read the state of Hall sensor.

        Returns:
            bool: True if magnetic field is detected, False otherwise.
        """
        return bool(self._pin.value())

    def set_callback(self, callback: callable) -> None:
        """
        设置磁场变化时的回调函数。

        Args:
            callback (callable): 用户回调函数。

        Notes:
            回调函数由 micropython.schedule 调度，避免在 IRQ 中直接运行耗时操作。

        ==========================================

        Set callback function for magnetic field change.

        Args:
            callback (callable): User callback function.

        Notes:
            Callback is scheduled via micropython.schedule to avoid heavy ops inside IRQ.
        """
        self._callback = callback

    def _irq_handler(self, pin: Pin) -> None:
        """
        内部方法：IRQ 中断处理函数。
        调用 micropython.schedule 调度用户回调函数。

        Args:
            pin (Pin): 触发中断的 GPIO 引脚对象。

        ==========================================

        Internal method: IRQ interrupt handler.
        Uses micropython.schedule to run user callback.

        Args:
            pin (Pin): GPIO pin object that triggered the interrupt.

        """
        if self._callback:
            micropython.schedule(self._scheduled_callback, 0)

    def _scheduled_callback(self, arg: int) -> None:
        """
        内部方法：真正执行用户回调。

        Args:
            arg (int): 占位参数，由 micropython.schedule 传入。

        ==========================================

        Internal method: Executes user callback.

        Args:
            arg (int): Placeholder argument from micropython.schedule.

        """
        if self._callback:
            self._callback()

    def enable(self) -> None:
        """
        启用霍尔传感器中断检测。
        Notes:
            默认在磁场变化（上升沿或下降沿）时触发。

        ==========================================

        Enable Hall sensor interrupt detection.

        Notes:
            Triggers on both rising and falling edges.
        """
        if self._irq is None:
            self._irq = self._pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
                                      handler=self._irq_handler)

    def disable(self) -> None:
        """
        禁用霍尔传感器中断检测。

        ==========================================

        Disable Hall sensor interrupt detection.

        """
        if self._irq:
            self._irq.handler(None)
            self._irq = None

    @property
    def digital(self) -> Pin:
        """

        获取绑定的数字引脚对象。

        Returns:
            Pin: 已绑定的 GPIO 引脚对象。

        ==========================================

        Get the bound digital pin object.

        Returns:
            Pin: Bound GPIO pin object.
        """
        return self._pin

# ======================================== 初始化配置 ============================================

# ======================================== 主程序 ===============================================
