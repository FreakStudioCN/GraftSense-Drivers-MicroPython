# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/29 下午6:47
# @Author  : 缪贵成
# @File    : pir_sensor1.py
# @Description : 红外人体热释传感器驱动
# @License : MIT

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import Pin
import time
import micropython

# ======================================== 自定义类 ============================================

class PIRSensor:
    """
    该类用于控制 PIR 红外运动传感器，支持中断回调、状态读取和阻塞等待。

    Attributes:
        _pin (Pin): machine.Pin 实例，用于读取 PIR 信号。
        _user_callback (callable): 用户回调函数，在检测到运动时触发。
        _irq_handler (object): 中断处理对象。
        _motion_detected (bool): 最近一次检测到的运动状态缓存。

    Methods:
        __init__(pin: int, callback: callable = None) -> None: 初始化传感器对象。
        pin() -> Pin: 返回底层 machine.Pin 对象。
        is_motion_detected() -> bool: 检查当前是否检测到运动。
        set_callback(callback: callable) -> None: 设置或更新运动检测回调。
        enable() -> None: 启用中断检测。
        disable() -> None: 禁用中断检测。
        wait_for_motion(timeout: int = None) -> bool: 阻塞等待运动，支持超时。
        debug() -> None: 打印调试信息。

    Notes:
        PIR 模块输出高电平表示检测到运动，低电平表示无运动。
        中断回调通过 micropython.schedule 调度到主线程执行。
        用户回调函数内不要执行耗时或阻塞操作。

    ==========================================

    PIR motion sensor driver class. Supports interrupt, polling, and blocking wait.

    Attributes:
        _pin (Pin): machine.Pin instance for PIR input.
        _user_callback (callable): user callback, triggered on motion detection.
        _irq_handler (object): IRQ handler object.
        _motion_detected (bool): cached motion state.

    Methods:
        __init__(pin: int, callback: callable = None) -> None: Initialize PIR sensor.
        pin() -> Pin: Return underlying Pin instance.
        is_motion_detected() -> bool: Check current motion state.
        set_callback(callback: callable) -> None: Set or update motion callback.
        enable() -> None: Enable motion interrupt.
        disable() -> None: Disable motion interrupt.
        wait_for_motion(timeout: int = None) -> bool: Block until motion detected.
        debug() -> None: Print debug info.

    Notes:
        High level = motion detected, low = no motion.
        Callbacks scheduled with micropython.schedule.
        Avoid long/blocking operations inside callback.
    """

    def __init__(self, pin: int, callback: callable = None) -> None:
        """
        初始化 PIR 传感器。
        Args:
            pin (int): GPIO 引脚编号。
            callback (callable, optional): 用户回调函数，在检测到运动时触发。
        Notes:
            如果传入 callback，会自动启用中断检测。
            初始化时 Pin 被配置为输入模式。

        ==========================================
        Initialize PIR sensor.
        Args:
            pin (int): GPIO pin number.
            callback (callable, optional): User callback, called on motion.
        Notes:
            - If callback is given, interrupt detection is enabled automatically.
            - Pin is configured as input during initialization.
        """
        # 配置 GPIO 引脚为输入
        self._pin = Pin(pin, Pin.IN)
        # 用户回调函数
        self._user_callback = callback
        # 中断处理对象
        self._irq_handler = None
        # 运动状态缓存
        self._motion_detected = False

        if callback:
            # 如果提供回调，启用中断
            self.enable()

    @property
    def pin(self) -> Pin:
        """
        返回底层 machine.Pin 对象。
        Returns:
            Pin: 底层 Pin 对象。

        ==========================================

        Return underlying machine.Pin object.

        Returns:
            Pin: Pin instance.
        """
        return self._pin

    def is_motion_detected(self) -> bool:
        """
        检查当前是否检测到运动。
        Returns:
            bool: True 表示检测到运动，False 表示未检测到。

        Notes:
            该方法直接读取引脚电平。
            建议在轮询模式下使用。

        ==========================================

        Check current motion state.

        Returns:
            bool: True if motion detected, False otherwise.

        Notes:
            Reads pin level directly.
            Useful in polling mode.
        """
        return self._pin.value() == 1

    def set_callback(self, callback: callable) -> None:
        """
        设置或更新运动检测回调函数。

        Args:
            callback (callable): 用户定义的回调函数，传入 None 表示禁用回调。
        Notes:
            设置新回调时会自动启用中断。
            传入 None 时会禁用中断。

        ==========================================

        Set or update motion detection callback.

        Args:
            callback (callable): User callback, or None to disable.

        Notes:
            Enabling callback also enables interrupt.
            Passing None disables interrupt.
        """
        self._user_callback = callback
        if callback:
            # 有回调就启用中断
            self.enable()
        else:
            # 没有回调就禁用中断
            self.disable()

    def _internal_irq_handler(self, pin) -> None:
        """
        内部中断处理函数，将用户回调调度到主线程。

        Args:
            pin (Pin): 触发中断的 Pin 对象。
        Notes:
            不要直接在此函数中执行耗时操作。
            回调被调度到主线程中执行。

        ==========================================

        Internal IRQ handler, schedules user callback.
        Args:
            pin (Pin): Pin that triggered IRQ.
        Notes:
            Do not perform heavy work here.
            Callback is scheduled into main thread.
        """
        self._motion_detected = True
        if self._user_callback:
            micropython.schedule(self._execute_callback, 0)

    def _execute_callback(self, arg: int) -> None:
        """
        调度执行用户回调函数。
        Args:
            arg (int): 调度参数（保留，未使用）。
        Notes:
            此方法在主线程上下文中执行。
            安全地调用用户定义的回调。

        ==========================================

        Execute user callback (scheduled).

        Args:
            arg (int): Placeholder argument, not used.

        Notes:
            Runs in main thread context.
            Safe to call user-defined callback here.
        """
        if self._user_callback:
            self._user_callback()

    def enable(self) -> None:
        """
        启用中断检测。
        Notes:
            使用 IRQ_RISING 触发。
            已经启用时再次调用无效。

        ==========================================

        Enable interrupt detection.

        Notes:
            Trigger mode: IRQ_RISING.
            Calling twice has no effect.
        """
        if not self._irq_handler:
            self._irq_handler = self._pin.irq(trigger=Pin.IRQ_RISING,
                                             handler=self._internal_irq_handler)

    def disable(self) -> None:
        """
        禁用中断检测。

        Notes:
            已经禁用时再次调用无效。

        ==========================================

        Disable interrupt detection.

        Notes:
            Calling twice has no effect.
        """
        if self._irq_handler:
            self._irq_handler.disable()
            self._irq_handler = None

    def wait_for_motion(self, timeout: int = None) -> bool:
        """
        阻塞等待检测到运动。
        Args:
            timeout (int, optional): 超时时间，单位毫秒。None 表示无限等待。

        Returns:
            bool: True 表示检测到运动，False 表示超时。

        Raises:
            RuntimeError: 传感器读取异常时。

        Notes:
            本方法使用轮询，每次检测间隔 10ms。
            阻塞主线程执行，不适合实时性要求高的场景。

        ==========================================

        Block until motion is detected.

        Args:
            timeout (int, optional): Timeout in ms. None means wait forever.

        Returns:
            bool: True if motion detected, False if timeout.

        Raises:
            RuntimeError: If sensor read fails.

        Notes:
            Polling with 10ms sleep.
            Blocking, avoid in real-time sensitive tasks.
        """
        start = time.ticks_ms()
        while True:
            if self.is_motion_detected():
                return True
            if timeout is not None:
                elapsed = time.ticks_diff(time.ticks_ms(), start)
                if elapsed >= timeout:
                    return False
                # 避免 CPU 空转
            time.sleep_ms(10)

    def debug(self) -> None:
        """
        打印调试信息：引脚值和运动状态。

        ==========================================

        Print debug info: pin value and motion state.

        """
        pin_val = self._pin.value()
        print(f"[DEBUG] PIR Pin: {self._pin}, Value: {pin_val}, Motion Detected: {self.is_motion_detesct()}")

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================