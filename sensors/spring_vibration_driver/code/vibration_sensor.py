# MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/22 下午4:08
# @Author  : 缪贵成
# @File    : vibration_sensor.py
# @Description : 弹簧震动开关驱动
# @License : MIT

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import micropython
import time
from machine import Pin

# ======================================== 全局变量 =============================================

# ======================================== 功能函数 =============================================

# ======================================== 自定义类 =============================================

class VibrationSensor:
    """
    滚珠震动传感器驱动类，支持震动检测、回调绑定和状态查询。
    Attributes:
        _pin (Pin): 绑定的数字 IO 引脚对象。
        _callback (callable): 用户自定义回调函数，在检测到震动时触发。
        last_state (bool): 上一次读取的传感器状态。
        debounce_ms (int): 消抖时间，单位毫秒。
        _irq (IRQ): 内部中断对象。
    Methods:
        __init__(self, pin: Pin, callback: callable = None, debounce_ms: int = 50) -> None:
            构造函数，绑定数字 IO 引脚，设置可选回调和消抖时间。
        init(self) -> None:
            初始化模块，配置引脚为输入，并启用中断（如果回调非空）。
        deinit(self) -> None:
            释放资源，禁用中断。
        read(self) -> bool:
            读取当前传感器状态，返回 True（检测到震动）或 False。
        _irq_handler(self, pin) -> None:
            内部中断处理函数，仅调用 micropython.schedule 调度用户回调。
        _scheduled_callback(self, arg) -> None:
            内部调度函数，真正执行用户回调。
        get_status(self) -> dict:
            返回状态字典，包括 {"last_state": bool, "debounce_ms": int, "callback_set": bool}。
    Notes:
        使用 _last_trigger 记录上次有效触发时间，用于消抖。
        _last_state 保存当前有效状态，可通过 get_status 查询。
        _irq_handler 内仅调度回调，避免 ISR 内耗时操作。

        ==========================================

        Ball-type vibration sensor driver class, supports vibration detection, callback binding, and status querying.
    Attributes:
        _pin (Pin): Digital IO pin object bound to the sensor.
        _callback (callable): User-defined callback triggered on vibration detection.
        last_state (bool): Last read sensor state.
        debounce_ms (int): Debounce time in milliseconds.
        _irq (IRQ): Internal interrupt object.

    Methods:
        __init__(self, pin: Pin, callback: callable = None, debounce_ms: int = 50) -> None:
            Constructor, bind digital IO pin, set optional callback and debounce time.
        init(self) -> None:
            Initialize module, configure pin as input, enable interrupt if callback is set.
        deinit(self) -> None:
            Release resources, disable interrupt.
        read(self) -> bool:
            Read current sensor state, return True if vibration detected, False otherwise.
        _irq_handler(self, pin) -> None:
            Internal interrupt handler, only schedules user callback with micropython.schedule.
        _scheduled_callback(self, arg) -> None:
            Internal scheduled function that actually executes user callback.
        get_status(self) -> dict:
            Return a status dictionary, including {"last_state": bool, "debounce_ms": int, "callback_set": bool}.

    Notes:

        _last_trigger stores the last valid trigger time for debounce handling.
        _last_state keeps the current valid state, accessible via get_status().
        _irq_handler only schedules the callback to avoid heavy ISR operations.
    """

    def __init__(self, pin: Pin, callback: callable = None, debounce_ms: int = 50) -> None:
        """
        初始化震动开关。

        Args:
            pin (Pin): 传感器接入的 GPIO 引脚对象。
            callback (callable, optional): 回调函数，在检测到震动时触发。
            debounce_ms (int, optional): 消抖时间，单位毫秒，默认 50。

        Notes:
            初始化状态变量 _last_state 和 _last_trigger。
            debounce_ms 控制触发间隔，避免抖动误触发。

        ==========================================

        Initialize vibration switch.

        Args:
            pin (Pin): GPIO pin object connected to vibration sensor.
            callback (callable, optional): Callback triggered on vibration.
            debounce_ms (int, optional): Debounce time in ms. Default 50.

        Notes:
            Initializes _last_state and _last_trigger.
            debounce_ms controls trigger interval to avoid false triggers.
        """
        self._pin = pin
        self._callback = callback
        self._debounce_ms = debounce_ms
        self._last_trigger = 0
        self._last_state = False
        self._irq = None

    def init(self) -> None:
        """
        初始化模块，引脚配置为输入，并在设置回调时启用中断。

        Notes:
            如果设置了回调函数，则启用 IRQ。
            中断触发类型为上升沿和下降沿，适应震动检测。

        ==========================================

        Initialize module. Configure pin as input and enable IRQ if callback is set.

        Notes:
            Enables IRQ if callback is set.
            IRQ triggers on rising and falling edges to detect vibration.
        """
        self._pin.init(Pin.IN)
        if self._callback:
            self._irq = self._pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
                                      handler=self._irq_handler)

    def deinit(self) -> None:
        """
        释放传感器资源，禁用中断。

        Notes:
            禁用 IRQ 并清除引用。

        ==========================================

        Release resources and disable IRQ.


        Notes:
            Disable IRQ and clear reference.
        """
        if self._irq:
            self._pin.irq(handler=None)
            self._irq = None

    def read(self) -> bool:
        """
        读取传感器状态。

        Returns:
            bool: True 表示检测到震动，False 表示未检测到。

        Notes:
            同步更新 _last_state。

        ==========================================

        Read sensor state.

        Returns:
            bool: True if vibration detected, False otherwise.

        Notes:
            Updates _last_state synchronously.
        """
        state = bool(self._pin.value())
        self._last_state = state
        return state

    def _irq_handler(self, pin: Pin) -> None:
        """
        内部方法：IRQ 触发时调度回调（带消抖）。

        Args:
            pin (Pin): 触发中断的引脚对象。
        Notes:

            仅在触发间隔超过 debounce_ms 时更新 _last_state。
            使用 micropython.schedule 调度回调，避免 ISR 内耗时操作。
            小于消抖时间的触发会被忽略。

        ==========================================

        Internal IRQ handler with debounce.

        Args:
            pin (Pin): Pin that triggered the interrupt.

        Notes:
            Updates _last_state only if interval > debounce_ms.
            Schedules callback using micropython.schedule to avoid heavy ISR work.
            Triggers within debounce interval are ignored.
        """
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_trigger) > self._debounce_ms:
            self._last_trigger = now
            self._last_state = bool(pin.value())
            if self._callback:
                micropython.schedule(self._scheduled_callback, 0)

    def _scheduled_callback(self, arg: int) -> None:
        """
        内部调度函数，在主线程中安全执行用户回调。

        Args:
            arg (int): 占位参数，由 micropython.schedule 传入。

        Notes:
            用户回调在主线程中执行，保证安全。
            arg 为 micropython.schedule 传入占位参数。

        ==========================================

        Internal scheduled callback. Executes user callback safely in main thread.

        Args:
            arg (int): Placeholder argument from micropython.schedule.

        Notes:
            Executes user callback safely in main thread.
            arg is placeholder provided by micropython.schedule.
        """
        if self._callback:
            self._callback()

    def get_status(self) -> dict:
        """
        返回传感器状态字典。

        Returns:
            dict: {"last_state": bool, "debounce_ms": int, "callback_set": bool}

        Notes:
            last_state 保存最后一次有效震动状态。
            debounce_ms 为当前设置的消抖时间。
            callback_set 表示是否绑定了回调函数。

        ==========================================
        Get sensor status dictionary.

        Returns:
            dict: {"last_state": bool, "debounce_ms": int, "callback_set": bool}

        Notes:
            last_state stores the last valid vibration state.
            debounce_ms is the configure
            callback_set indicates if a callback function is bound.
        """
        return {
            "last_state": self._last_state,
            "debounce_ms": self._debounce_ms,
            "callback_set": self._callback is not None
        }

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ==============================================
