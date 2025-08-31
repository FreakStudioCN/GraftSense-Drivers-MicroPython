# MicroPython v1.23.0
# -*- coding: utf-8 -*-   
# @Time    : 2025/8/23 下午5:55
# @Author  : 缪贵成
# @File    : flame_sensor.py
# @Description : 火焰传感器驱动文件
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import time
import micropython
from machine import Pin, ADC

# ======================================== 全局变量 =============================================

# ======================================== 功能函数 =============================================

# ======================================== 自定义类 =============================================

class FlameSensor:
    """
    火焰传感器驱动类，支持数字 DO 火焰触发检测、模拟 AO 读数以及回调绑定。

    Attributes:
        _digital_pin (Pin): 绑定的数字输出引脚对象（DO）。
        _analog_pin (ADC): 绑定的模拟输出引脚对象（AO）。
        _callback (callable): 用户自定义的回调函数，在火焰检测到时触发。
        _irq (IRQ): 内部中断对象。
        _last_trigger (int): 上一次触发时间，用于消抖或防抖。

    Methods:
        __init__(analog_pin: int, digital_pin: int, callback: callable = None) -> None:
            初始化传感器，绑定 AO/DO 引脚，设置回调。
        is_flame_detected() -> bool:
            读取数字引脚 DO 状态，返回是否检测到火焰。
        get_analog_value() -> int:
            获取 AO 引脚原始 ADC 值。
        get_voltage() -> float:
            将 AO 原始值转换为电压（单位 V）。
        set_callback(callback: callable) -> None:
            设置数字触发回调函数。
        enable() -> None:
            启用数字引脚中断。
        disable() -> None:
            禁用数字引脚中断。
        wait_for_flame(timeout: int = None) -> bool:
            阻塞等待火焰触发，可设置超时。
        digital (property) -> Pin:
            返回数字引脚对象。
        analog (property) -> ADC:
            返回模拟引脚对象。

    Notes:
        数字引脚中断默认未启用，需要调用 enable()。
        回调函数会在主线程中执行，避免 ISR 阻塞。
        get_voltage() 基于 3.3V ADC，非阻塞操作。
        wait_for_flame() 是阻塞方法，适合测试或同步触发场景。

    ==========================================

    Flame sensor driver class. Supports digital DO flame detection, analog AO reading, and callback binding.

    Attributes:
        _digital_pin (Pin): Digital output pin object (DO).
        _analog_pin (ADC): Analog output pin object (AO).
        _callback (callable): User-defined callback triggered on flame detection.
        _irq (IRQ): Internal interrupt object.
        _last_trigger (int): Last trigger timestamp, for debounce.

    Methods:
        __init__(analog_pin: int, digital_pin: int, callback: callable = None) -> None:
            Initialize sensor, bind AO/DO pins, set callback.
        is_flame_detected() -> bool:
            Read digital pin DO, return True if flame detected.
        get_analog_value() -> int:
            Get raw ADC value from AO.
        get_voltage() -> float:
            Convert AO raw value to voltage (V).
        set_callback(callback: callable) -> None:
            Set callback function triggered on digital flame detection.
        enable() -> None:
            Enable digital pin IRQ.
        disable() -> None:
            Disable digital pin IRQ.
        wait_for_flame(timeout: int = None) -> bool:
            Blocking wait for flame detection, optional timeout.
        digital (property) -> Pin:
            Return digital pin object.
        analog (property) -> ADC:
            Return analog pin object.

    Notes:
        Digital pin IRQ not enabled by default; call enable() to activate.
        User callback executes in main thread, ISR-safe.
        get_voltage() is non-blocking and based on 3.3V ADC.
        wait_for_flame() blocks, suitable for testing or synchronous trigger.
    """

    def __init__(self, analog_pin: int, digital_pin: int, callback: callable = None) -> None:
        """

        初始化火焰传感器 AO/DO 引脚并设置回调函数。

        Args:
            analog_pin (int): AO 引脚编号。
            digital_pin (int): DO 引脚编号。
            callback (callable, optional): 火焰触发回调函数。
        Notes:
            默认未启用中断，需要调用 enable()。
        ==========================================

        Initialize flame sensor AO/DO pins and optional callback.
        Args:
            analog_pin (int): AO pin number.
            digital_pin (int): DO pin number.
            callback (callable, optional): Callback triggered on flame detection.

        Notes:
            IRQ not enabled by default, call enable() to activate.
        """
        self._analog_pin = ADC(analog_pin)
        self._digital_pin = Pin(digital_pin, Pin.IN)
        self._callback = callback
        self._irq = None
        self._last_trigger = 0

    def is_flame_detected(self) -> bool:
        """
        读取数字 DO 引脚状态。
        Returns:
            bool: True 表示检测到火焰，False 表示未检测到。

        ==========================================

        Read digital pin DO state.
        Returns:
            bool: True if flame detected, False otherwise.
        """
        return bool(self._digital_pin.value())

    def get_analog_value(self) -> int:
        """
        获取 AO 引脚原始 ADC 值。
        Returns:
            int: AO 数值。

        ==========================================
        Get raw ADC value from AO pin.

        Returns:
            int: AO value.
        """
        return self._analog_pin.read_u16()

    def get_voltage(self) -> float:
        """
        将 AO 原始值转换为电压（单位 V）。
        Returns:
            float: 电压值。

        ==========================================

        Convert AO value to voltage (V).

        Returns:
            float: Voltage value.
        """
        return self.get_analog_value() / 65535 * 3.3

    def set_callback(self, callback: callable) -> None:
        """
        设置火焰触发回调函数。

        Args:
            callback (callable): 用户回调函数。
        ==========================================

        Set callback function triggered on digital flame detection.

        Args:
            callback (callable): User callback function.
        """
        self._callback = callback

    def _irq_handler(self, pin: Pin) -> None:
        """
        内部方法：数字引脚 IRQ 中断处理函数。
        仅更新时间标志和检测状态，避免在 ISR 内进行耗时操作。
        使用 micropython.schedule 调度用户回调。

        Args:
            pin (Pin): 触发中断的 GPIO 引脚对象。

        Notes:
            ISR 内只更新状态，不打印或做阻塞操作。
            调度用户回调在主线程执行，安全防止 ISR 阻塞。

        ==========================================

        Internal method: Digital pin IRQ interrupt handler.
        Only updates status flags and detection state. Avoids heavy operations in ISR.
        Schedules user callback using micropython.schedule.

        Args:
            pin (Pin): GPIO pin object that triggered the interrupt.

        Notes:
            Only update flags in ISR, do not print or block.
            User callback is scheduled to run in main thread for safety.
        """
        # 更新火焰检测状态
        self._flame_detected = pin.value() == 1

        # 仅更新时间/状态标志，不打印
        # 表示事件已触发
        self._event_flag = True
        # 调度用户回调
        if self._callback:
            micropython.schedule(self._scheduled_callback, 0)

    def _scheduled_callback(self, arg: int) -> None:
        """
        内部调度函数，由 micropython.schedule 调用，在主线程中安全执行用户回调。

        Args:
            arg (int): 占位参数，由 micropython.schedule 传入。
        Notes:
            避免在 ISR 内执行耗时操作。
            用户回调可安全执行打印、控制 LED 等操作。

        ==========================================

        Internal scheduled function called by micropython.schedule. Executes user callback safely in main thread.

        Args:
            arg (int): Placeholder argument passed by micropython.schedule.
        Notes:
            Avoid heavy operations inside ISR.
            User callback can safely perform printing, LED control, etc.
        """
        if self._callback:
            self._callback()

    def enable(self) -> None:
        """
        启用数字中断检测。
        ==========================================

        Enable digital pin IRQ.

        """
        if self._irq is None:
            self._irq = self._digital_pin.irq(trigger=Pin.IRQ_FALLING, handler=self._irq_handler)

    def disable(self) -> None:
        """
        禁用数字中断检测。
        ==========================================

        Disable digital pin IRQ.

        """
        if self._irq:
            self._digital_pin.irq(handler=None)
            self._irq = None

    def wait_for_flame(self, timeout: int = None) -> bool:
        """

        阻塞等待火焰触发信号，可设置超时。

        Args:
            timeout (int, optional): 超时秒数，默认无限等待。

        Returns:
            bool: True 表示检测到火焰，False 表示超时或未检测到。

        ==========================================
        Blocking wait for flame detection, with optional timeout.

        Args:
            timeout (int, optional): Timeout in seconds, default is None (wait indefinitely).

        Returns:
            bool: True if flame detected, False if timeout or no detection.
        """
        start = time.time()
        while True:
            if self.is_flame_detected():
                return True
            if timeout and (time.time() - start) > timeout:
                return False
            time.sleep(0.05)

    @property
    def digital(self) -> Pin:
        """
        获取数字引脚对象。

        Returns:
            Pin: 数字引脚对象。

        ==========================================

        Get digital pin object.

        Returns:
            Pin: Digital pin object.
        """
        return self._digital_pin

    @property
    def analog(self) -> ADC:
        """

        获取模拟引脚对象。

        Returns:
            ADC: 模拟引脚对象。

        ==========================================

        Get analog pin object.

        Returns:
            ADC: Analog pin object.
        """
        return self._analog_pin

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ==============================================
