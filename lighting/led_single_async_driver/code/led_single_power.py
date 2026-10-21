# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/25 上午11:52
# @Author  : 缪贵成
# @File    : led_single_power.py
# @Description : 大功率单颗LED驱动
# @License : MIT

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import Pin, PWM
import time

# ======================================== 全局变量 =============================================

# ======================================== 功能函数 =============================================

# ======================================== 自定义类 =============================================


class PowerLED:
    """
    单颗功率 LED 驱动类，支持全开、关闭、亮度调节及状态查询。

    Attributes:
        _pin (Pin): 绑定的数字 GPIO 引脚对象。
        _pwm (PWM): PWM 对象，用于亮度调节。
        _state (bool): LED 当前状态，True 表示亮，False 表示灭。
        _pwm_freq (int): PWM 频率，单位 Hz。

    Methods:
        on() -> None: 打开 LED（全亮）。
        off() -> None: 关闭 LED。
        toggle() -> None: 切换 LED 状态。
        set_brightness(duty: int) -> None: 设置 PWM 亮度，0-1023。
        get_state() -> bool: 获取 LED 当前状态。

    Notes:
        PWM 对象在初始化时创建，非 ISR-safe。
        方法中操作 Pin/PWM 对象均非 ISR-safe。
        不要在 ISR 中直接调用 PWM 写操作，可使用 micropython.schedule 延迟。

    ==========================================

    Single Power LED driver class. Supports full on/off, brightness control, and state query.

    Attributes:
        _pin (Pin): Digital GPIO pin object.
        _pwm (PWM): PWM object for brightness control.
        _state (bool): Current LED state, True = on, False = off.
        _pwm_freq (int): PWM frequency in Hz.

    Methods:
        on() -> None: Turn LED fully on.
        off() -> None: Turn LED off.
        toggle() -> None: Toggle LED state.
        set_brightness(duty: int) -> None: Set PWM brightness, 0-1023.
        get_state() -> bool: Get current LED state.

    Notes:
        PWM object creation is non ISR-safe.
        Pin/PWM operations are non ISR-safe.
        Use micropython.schedule if calling from ISR.
    """

    def __init__(self, pin: int, pwm_freq: int = 1000) -> None:
        """
        初始化 Power LED 对象，绑定 GPIO 引脚并创建 PWM。
        Args:
            pin (int): LED 连接的 GPIO 引脚编号。
            pwm_freq (int, optional): PWM 频率，默认 1000 Hz。

        Raises:
            ValueError: 当 pwm_freq 不在合理范围时。

        Notes:
            创建 PWM 对象，非 ISR-safe。

        ==========================================

        Initialize PowerLED object, bind GPIO pin and create PWM.

        Args:
            pin (int): GPIO pin number where LED is connected.
            pwm_freq (int, optional): PWM frequency in Hz, default 1000 Hz.

        Raises:
            ValueError: If pwm_freq is out of valid range.

        Notes:
            PWM object creation is non ISR-safe.
        """
        if pwm_freq <= 0 or pwm_freq > 1000:
            raise ValueError("PWM frequency out of range (1-1000 Hz)")

        # 判断传入的pin是不是数字
        if not isinstance(pin, int):
            raise ValueError("Pin must be an integer")

        self._pin = Pin(pin, Pin.OUT)
        self._pwm_freq = pwm_freq
        self._pwm = PWM(self._pin)
        self._pwm.freq(self._pwm_freq)
        self._state = False
        self._pwm.duty_u16(0)

    def on(self) -> None:
        """
        打开 LED（全亮）。

        Raises:
            RuntimeError: PWM 写入失败。

        ==========================================

        Turn LED fully on.

        Raises:
            RuntimeError: PWM write failure.
        """
        try:
            self._pwm.duty_u16(65535)
            self._state = True
        except Exception as e:
            raise RuntimeError("Failed to turn LED on") from e

    def off(self) -> None:
        """
        关闭 LED。

        Raises:
            RuntimeError: PWM 写入失败。

        ==========================================

        Turn LED off.

        Raises:
            RuntimeError: PWM write failure.

        """
        try:
            self._pwm.duty_u16(0)
            self._state = False
        except Exception as e:
            raise RuntimeError("Failed to turn LED off") from e

    def toggle(self) -> None:
        """
        切换 LED 状态（开/关）。

        Raises:
            RuntimeError: PWM 写入失败。

        ==========================================

        Toggle LED state.

        Raises:
            RuntimeError: PWM write failure.
        """
        if self._state:
            self.off()
        else:
            self.on()

    def set_brightness(self, duty: int) -> None:
        """
        设置 PWM 亮度。

        Args:
            duty (int): PWM 占空比 0-1023。

        Raises:
            ValueError: duty 不在 0-1023 范围。
            RuntimeError: PWM 写入失败。
        Notes:
            非 ISR-safe。

        ==========================================

        Set PWM brightness.
        Args:
            duty (int): PWM duty cycle 0-1023.

        Raises:
            ValueError: If duty not in 0-1023.
            RuntimeError: PWM write failure.

        Notes:
            Not ISR-safe.
        """
        if duty < 0 or duty > 1023:
            raise ValueError("Duty must be 0-1023")
        try:
            duty16 = int(duty * 65535 / 1023)
            self._pwm.duty_u16(duty16)
            self._state = duty > 0
        except Exception as e:
            raise RuntimeError("Failed to set LED brightness") from e

    def get_state(self) -> bool:
        """
        获取 LED 当前状态。

        Returns:
            bool: True 表示亮，False 表示灭。

        Notes:
            仅返回内部状态，非 ISR-safe。

        ==========================================

        Get current LED state.

        Returns:
            bool: True = on, False = off.

        Notes:
            - Returns internal state only, not ISR-safe.
        """
        return self._state

    @property
    def digital(self) -> Pin:
        """
        返回数字引脚对象。

        Returns:
            Pin: LED 绑定的 GPIO 引脚对象。
        ==========================================

        Get digital pin object.

        Returns:
            Pin: Bound GPIO pin object.
        """
        return self._pin

    @property
    def pwm(self) -> PWM:
        """
        返回 PWM 对象。

        Returns:
            PWM: 用于调光的 PWM 对象。

        ==========================================

        Get PWM object.

        Returns:
            PWM: PWM object for brightness control.
        """
        return self._pwm


# ======================================== 初始化配置 ============================================

# ======================================== 主程序 ===============================================
