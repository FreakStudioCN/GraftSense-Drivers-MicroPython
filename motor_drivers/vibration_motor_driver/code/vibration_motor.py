# MicroPython v1.23.0
# -*- coding: utf-8 -*-   
# @Time    : 2025/8/26 上午11:41
# @Author  : 缪贵成
# @File    : vibration_motor.py
# @Description : 震动马达驱动文件
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import Pin, PWM

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class VibrationMotor:
    """
    震动马达控制类，提供开关控制和 PWM 强度调节功能。
    Attributes:
        _digital (Pin): 控制引脚对象。
        _pwm (PWM): PWM 对象，用于强度调节。
        _state (bool): 当前震动状态，True=震动中，False=停止。

    Methods:
        __init__(pin: int, pwm_freq: int = 1000) -> None: 初始化震动马达。
        on() -> None: 启动震动马达（全速）。
        off() -> None: 停止震动马达。
        toggle() -> None: 切换震动状态。
        set_brightness(duty: int) -> None: 设置震动强度（0-1023）。
        get_state() -> bool: 获取当前状态。
        digital() -> Pin: 返回控制引脚对象。
        pwm() -> PWM: 返回 PWM 对象。

    Notes:
        PWM 分辨率为 10 位（0–1023），在 Pico 上使用 duty_u16 映射为 16 位。
        调用 PWM 方法非 ISR-safe。
        初始化时马达默认停止。

    ==========================================

    Vibration motor driver class, supports on/off and PWM intensity control.

    Attributes:
        _digital (Pin): Control pin object.
        _pwm (PWM): PWM object for intensity.
        _state (bool): Current state, True=ON, False=OFF.

    Methods:
        __init__(pin: int, pwm_freq: int = 1000) -> None: Initialize vibration motor.
        on() -> None: Turn on motor at full speed.
        off() -> None: Turn off motor.
        toggle() -> None: Toggle motor state.
        set_brightness(duty: int) -> None: Set intensity (0-1023).
        get_state() -> bool: Get current state.
        digital() -> Pin: Return control Pin object.
        pwm() -> PWM: Return PWM object.

    Notes:
        PWM resolution 10-bit (0–1023).
        PWM calls not ISR-safe.
        Default state is OFF.
    """

    def __init__(self, pin: int, pwm_freq: int = 1000):
        """
        初始化震动马达。

        Args:
            pin (int): 控制引脚号。
            pwm_freq (int, optional): PWM 频率，默认 1000Hz。

        Notes:
            初始化时马达默认停止。

        ==========================================
        Initialize vibration motor.

        Args:
            pin (int): Control pin number.
            pwm_freq (int, optional): PWM frequency in Hz, default 1000.

        Notes:
            Motor is OFF by default after initialization.
        """
        self._digital = Pin(pin, Pin.OUT)
        self._pwm = PWM(self._digital)
        self._pwm.freq(pwm_freq)
        self._pwm.duty_u16(0)
        self._state = False

    def on(self) -> None:
        """
        启动震动马达（全速）。

        Notes:
            设置 PWM 占空比为最大值 1023。
        ==========================================

        Turn on motor at full speed.

        Notes:
            Sets PWM duty to maximum (1023).
        """
        self._pwm.duty_u16(1023 * 64)
        self._state = True

    def off(self) -> None:
        """
        停止震动马达。

        Notes:
            设置 PWM 占空比为 0。
        ==========================================

        Turn off motor.
        Notes:
            Sets PWM duty to 0.
        """
        self._pwm.duty_u16(0)
        self._state = False

    def toggle(self) -> None:
        """
        切换震动马达状态。

        Notes:
            根据当前状态调用 on() 或 off()。

        ==========================================

        Toggle motor state.

        Notes:
            Calls on() if currently OFF, or off() if currently ON.
        """
        if self._state:
            self.off()
        else:
            self.on()

    def set_brightness(self, duty: int) -> None:
        """
        设置震动强度。

        Args:
            duty (int): PWM 占空比，范围 0–1023。

        Raises:
            ValueError: duty 超出 0-1023 范围。

        Notes:
            不改变 _state，只调节强度。

        ==========================================

        Set vibration intensity.

        Args:
            duty (int): PWM duty cycle, range 0–1023.

        Raises:
            ValueError: If duty is outside 0-1023.

        Notes:
            Does not change _state, only adjusts intensity.
        """
        if not (0 <= duty <= 1023):
            raise ValueError("PWM duty must be 0-1023")
        self._pwm.duty_u16(duty * 64)  # 修改为 Pico 兼容

    def get_state(self) -> bool:
        """
        获取当前震动马达状态。

        Returns:
            bool: True 表示震动中，False 表示停止。

        ==========================================

        Get current motor state.

        Returns:
            bool: True=ON, False=OFF.

        """
        return self._state

    @property
    def digital(self) -> Pin:
        """
        返回绑定的控制引脚对象。
        Returns:
            Pin: 控制引脚对象。
        ==========================================

        Return control Pin object.
        Returns:
            Pin: Control pin.
        """
        return self._digital

    @property
    def pwm(self) -> PWM:
        """
        返回绑定的 PWM 对象。
        Returns:
            PWM: PWM 对象，用于强度调节。

        ==========================================
        Return PWM object.
        Returns:
            PWM: PWM object.
        """
        return self._pwm

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================