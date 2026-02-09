# MicroPython v1.23.0
# -*- coding: utf-8 -*-   
# @Time    : 2025/9/4 上午9:42
# @Author  : 缪贵成
# @File    : tcr5000.py
# @Description :基于TCR5000L的单路循迹模块驱动程序
# @License : MIT

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import Pin
import micropython

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class TCR5000:
    """
    该类控制 TCR5000L 光电反射式循迹传感器，提供电平读取和中断回调功能。

    Attributes:
        _pin (Pin): machine.Pin 实例，用于读取传感器数字信号。
        _callback (function|None): 用户注册的回调函数，参数为电平值。
        _irq (object|None): 中断对象，负责硬件电平变化检测。

    Methods:
        __init__(pin: int, *, trigger: int = Pin.IRQ_FALLING | Pin.IRQ_RISING) -> None:
            初始化传感器引脚并配置中断触发模式。
        read() -> int:
            读取当前电平，返回 0 或 1。
        set_callback(func: function) -> None:
            注册用户回调函数，在电平变化时调度执行。
        deinit() -> None:
            注销中断并释放资源。

    Notes:
        本类使用 micropython.schedule 将回调调度到主循环执行，避免在 ISR 内直接运行。
        电平含义依模块设计可能不同，一般 0=黑线，1=白底。

    ==========================================

    TCR5000L reflective optical line tracking sensor driver. Supports digital read and interrupt callbacks.

    Attributes:
        _pin (Pin): machine.Pin instance for reading sensor digital output.
        _callback (function|None): User callback function, parameter is level.
        _irq (object|None): IRQ object for hardware level change detection.

    Methods:
        __init__(pin: int, *, trigger: int = Pin.IRQ_FALLING | Pin.IRQ_RISING) -> None:
            Initialize sensor pin and configure interrupt mode.
        read() -> int:
            Read current level (0 or 1).
        set_callback(func: function) -> None:
            Register user callback, scheduled on level change.
        deinit() -> None:
            Disable interrupt and release resources.

    Notes:
        Uses micropython.schedule to defer callbacks to main loop, avoiding ISR execution.
        Level meaning depends on module design, typically 0=black line, 1=white background.
    """

    def __init__(self, pin: int, *, trigger: int = Pin.IRQ_FALLING | Pin.IRQ_RISING) -> None:
        """
        初始化 TCR5000 传感器。

        Args:
            pin (int): 传感器信号脚连接的 GPIO 引脚编号。
            trigger (int): 中断触发方式，默认为下降沿和上升沿。

        Notes:
            本方法会配置 GPIO 并注册硬件中断。

        ==========================================

        Initialize TCR5000 sensor.

        Args:
            pin (int): GPIO pin number connected to sensor output.
            trigger (int): Interrupt trigger mode, default rising and falling edges.

        Notes:
            This method configures GPIO and attaches interrupt.
        """
        self._pin = Pin(pin, Pin.IN)
        self._callback = None
        self._irq = self._pin.irq(handler=self._irq_handler, trigger=trigger)

    def read(self) -> int:
        """
        读取当前电平。

        Returns:
            int: 当前电平，0 或 1。

        Notes:
            调用开销极小，可在主循环频繁调用。

        ==========================================

        Read current digital level.

        Returns:
            int: Current level, 0 or 1.

        Notes:
            Very lightweight, safe for frequent calls in main loop.
        """
        return self._pin.value()

    def set_callback(self, func) -> None:
        """
        注册用户回调函数。

        Args:
            func (function): 用户函数，签名为 func(value: int)，参数为当前电平。

        Raises:
            TypeError: 如果 func 不是可调用对象。

        Notes:
            回调在电平变化时调度执行。
            使用 micropython.schedule 在主循环中执行。

        ==========================================

        Register user callback.

        Args:
            func (function): User function with signature func(value: int).

        Raises:
            TypeError: If func is not callable.

        Notes:
            Callback scheduled on level change.
            Executed in main loop via micropython.schedule.
        """
        if not callable(func):
            raise TypeError("callback must be callable")
        self._callback = func

    def _irq_handler(self, pin: Pin) -> None:
        """
        内部中断处理函数，用于捕获传感器电平变化并调度回调执行。

        Args:
            pin (Pin): 触发中断的引脚对象。

        Notes:
            该方法在中断上下文执行，不应包含耗时操作。
            实际用户回调通过 micropython.schedule 延迟到安全上下文中执行。

        ==========================================

        Internal interrupt handler for sensor signal change.

        Args:
            pin (Pin): Pin instance that triggered the interrupt.

        Notes:
            Executed in ISR context, must be lightweight.
            Actual user callback is deferred to safe context via micropython.schedule.
        """
        if self._callback:
            micropython.schedule(self._scheduled_callback, pin.value())

    def _scheduled_callback(self, value: int) -> None:
        """
        在调度上下文中执行用户注册的回调函数。

        Args:
            value (int): 当前引脚电平，0 或 1。

        Notes:
            在安全上下文中执行，避免 ISR 中调用不安全操作。
            如果未设置回调函数则不执行任何操作。

        ==========================================

        Run user callback in scheduled (non-ISR) context.

        Args:
            value (int): Current pin value, 0 or 1.

        Notes:
            Safe to run, avoids unsafe operations in ISR.
            No action if no callback was registered.
        """
        if self._callback:
            self._callback(value)

    def deinit(self) -> None:
        """
        注销中断并释放资源。

        Notes:
            调用后不可再使用 read() 或 set_callback()，需重新初始化。

        ==========================================

        Deinitialize interrupt and release resources.

        Notes:
            After deinit, read() and set_callback() are unavailable.
            Reinitialize if needed again.
        """
        if self._irq:
            self._irq.handler(None)
            self._irq = None
        self._callback = None

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
