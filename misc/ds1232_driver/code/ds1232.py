# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2025/8/25 下午6:46   
# @Author  : 李清水            
# @File    : ds1232.py       
# @Description : 外部DS1232看门狗模块驱动程序

# ======================================== 导入相关模块 =========================================

# 导入硬件相关模块
from machine import Pin, Timer

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class DS1232:
    """
    该类控制外部 DS1232 看门狗模块，通过周期性翻转 WDI 引脚喂狗，避免 MCU 被复位。

    Attributes:
        wdi (Pin): machine.Pin 实例，用于输出喂狗脉冲。
        state (int): 当前 WDI 引脚输出状态，0 或 1。
        timer (Timer): machine.Timer 实例，用于周期性喂狗。

    Methods:
        __init__(wdi_pin: int, feed_interval: int = 1000) -> None: 初始化看门狗并启动定时喂狗。
        stop() -> None: 停止自动喂狗，将 WDI 引脚置低。
        kick() -> None: 手动喂狗，立即翻转一次 WDI 引脚。

    Notes:
        - 初始化时会创建 Timer 对象以定时翻转 WDI。
        - _feed 为内部回调方法，不建议直接调用。
        - 该类方法大多非 ISR-safe，Timer 回调 _feed 是 ISR-safe。
        - stop() 后 WDI 引脚保持低电平，DS1232 将在超时后复位 MCU。

    ==========================================

    DS1232_Watchdog driver for controlling an external DS1232 watchdog module.
    Periodically toggles WDI pin to prevent MCU reset.

    Attributes:
        wdi (Pin): machine.Pin instance for feeding pulses.
        state (int): Current WDI output state, 0 or 1.
        timer (Timer): machine.Timer instance for periodic feeding.

    Methods:
        __init__(wdi_pin: int, feed_interval: int = 1000) -> None: Initialize the watchdog and start automatic feeding.
        stop() -> None: Stop automatic feeding and set WDI low.
        kick() -> None: Manually feed the watchdog by toggling WDI once.

    Notes:
        - Initializes a Timer to periodically toggle WDI.
        - _feed is an internal callback method, not recommended for direct user call.
        - Most methods are not ISR-safe; _feed callback is ISR-safe.
        - After stop(), WDI remains low; DS1232 will reset MCU on timeout.
    """

    def __init__(self, wdi_pin: int, feed_interval: int = 1000) -> None:
        """
        初始化 DS1232 看门狗。

        Args:
            wdi_pin (int): WDI 引脚编号。
            feed_interval (int): 喂狗间隔时间，单位 ms。默认 1000ms。

        Returns:
            None

        Raises:
            ValueError: 当 wdi_pin 非整数或 feed_interval > 1000 时。
            RuntimeError: Timer 初始化失败时。

        Notes:
            创建对象后会立即启动定时喂狗。
            调用会涉及定时器资源，非 ISR-safe。

        ==========================================

        Initialize DS1232 watchdog.

        Args:
            wdi_pin (int): WDI pin number.
            feed_interval (int): Feeding interval in ms. Default is 1000ms.

        Returns:
            None

        Raises:
            ValueError: If wdi_pin is not an integer or feed_interval > 1000 ms.
            RuntimeError: If Timer initialization fails.

        Notes:
            Feeding starts immediately after object creation.
            Uses Timer resource, not ISR-safe.
        """
        # 参数检查
        if not isinstance(wdi_pin, int):
            raise ValueError("wdi pin must be an integer")
        if feed_interval > 1000:
            raise ValueError("feed_interval must be less than 1000ms")

        self.wdi = Pin(wdi_pin, Pin.OUT)
        # 当前输出状态
        self.state = 0
        self.timer = Timer(-1)

        # 启动定时器，周期性喂狗
        self.timer.init(period=feed_interval, mode=Timer.PERIODIC, callback=self._feed)

    def _feed(self, t: Timer) -> None:
        """
        定时器回调函数：周期性翻转 WDI 引脚。

        Args:
            t (Timer): 触发本回调的定时器对象。

        Returns:
            None

        Raises:
            None

        Notes:
            内部方法，不建议用户直接调用。
            在中断上下文中执行，ISR-safe。

        ==========================================

        Timer callback: toggle WDI pin periodically.

        Args:
            t (Timer): Timer instance triggering this callback.

        Returns:
            None

        Raises:
            None

        Notes:
            Internal method, not recommended for direct user call.
            Runs in interrupt context, ISR-safe.
        """
        # 翻转 0/1
        self.state ^= 1
        self.wdi.value(self.state)

    def stop(self) -> None:
        """
        停止自动喂狗。

        Args:
            None

        Returns:
            None

        Raises:
            RuntimeError: 当定时器释放失败时。

        Notes:
            停止后 WDI 引脚保持低电平，DS1232 将会在超时后复位 MCU。

        ==========================================

        Stop automatic feeding.

        Args:
            None

        Returns:
            None

        Raises:
            RuntimeError: If timer deinitialization fails.

        Notes:
            WDI pin is held low after stopping, DS1232 will reset MCU on timeout.
        """
        self.timer.deinit()
        self.wdi.value(0)

    def kick(self) -> None:
        """
        手动喂狗：立即翻转一次 WDI 引脚。

        Args:
            None

        Returns:
            None

        Raises:
            RuntimeError: 当引脚写入失败时。

        Notes:
            通常用于临时喂狗，或在停止自动喂狗后手动维持。

        ==========================================

        Manually feed watchdog by toggling WDI once.

        Args:
            None

        Returns:
            None

        Raises:
            RuntimeError: If pin write fails.

        Notes:
            Useful for temporary feeding or manual feeding after stopping auto mode.
        """
        self.state ^= 1
        self.wdi.value(self.state)

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================