# MicroPython v1.23.0
# -*- coding: utf-8 -*-   
# @Time    : 2025/8/26 上午10:45
# @Author  : 缪贵成
# @File    : uv_matrix.py
# @Description : uv紫外灯矩阵模块驱动文件,参考代码:https://github.com/TimHanewich/MicroPython-Collection/tree/master/GUVA-S12SD
# @License : MIT

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import Pin, PWM

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class UVMatrix:
    """
    UV 矩阵控制类，提供开关控制和 PWM 调光功能。
    Attributes:
        _digital (Pin): MOSFET 控制引脚。
        _pwm (PWM): PWM 对象，用于亮度调节。
        _state (bool): 当前 UV 矩阵状态，True 表示亮，False 表示灭。

    Methods:
        __init__(pin: int, pwm_freq: int = 1000) -> None: 初始化 UV 矩阵。
        on() -> None: 打开 UV 矩阵。
        off() -> None: 关闭 UV 矩阵。
        toggle() -> None: 切换 UV 矩阵状态。
        set_brightness(duty: int) -> None: 设置亮度，范围 0–1023。
        get_state() -> bool: 获取当前状态。
        digital() -> Pin: 返回 MOSFET 控制引脚对象。
        pwm() -> PWM: 返回 PWM 对象。

    Notes:
        PWM 分辨率为 10 位（0-1023）。
        调用 PWM 方法需注意 ISR 安全性。
        默认初始化为关闭状态。

    ==========================================

    UV Matrix driver class, supports on/off and PWM brightness control.

    Attributes:
        _digital (Pin): MOSFET control pin.
        _pwm (PWM): PWM object for brightness control.
        _state (bool): Current state, True=ON, False=OFF.

    Methods:
        __init__(pin: int, pwm_freq: int = 1000) -> None: Initialize UV matrix.
        on() -> None: Turn on UV matrix.
        off() -> None: Turn off UV matrix.
        toggle() -> None: Toggle state.
        set_brightness(duty: int) -> None: Set brightness (0-1023).
        get_state() -> bool: Get current state.
        digital() -> Pin: Return control Pin object.
        pwm() -> PWM: Return PWM object.

    Notes:
        PWM resolution is 10-bit (0-1023).
        PWM calls are not ISR-safe.
        Default state is OFF.
    """

    def __init__(self, pin: int, pwm_freq: int = 1000):
        """
        初始化 UV 矩阵。
        Args:
            pin (int): MOSFET 控制引脚号。
            pwm_freq (int, optional): PWM 频率，默认 1000 Hz。
        Notes:
            初始化时 UV 矩阵默认关闭。

        ==========================================

        Initialize UV matrix.
        Args:
            pin (int): MOSFET control pin number.
            pwm_freq (int, optional): PWM frequency in Hz, default 1000.
        Notes:
            UV matrix is OFF by default after initialization.
        """
        self._digital = Pin(pin, Pin.OUT)
        self._pwm = PWM(self._digital)
        self._pwm.freq(pwm_freq)
        self._pwm.duty_u16(0)
        self._state = False

    def on(self) -> None:
        """
        打开 UV 矩阵（全亮）。
        Notes:
            设置 PWM 占空比为最大值 1023。

        ==========================================

        Turn on UV matrix at full brightness.
        Notes:
            Sets PWM duty to maximum (1023).
        """
        # 最高只能占空比一半
        self._pwm.duty_u16(32766)
        self._state = True

    def off(self) -> None:
        """
        关闭 UV 矩阵。
        Notes:
            设置 PWM 占空比为 0。

        ==========================================

        Turn off UV matrix.
        Notes:
            Sets PWM duty to 0.
        """
        self._pwm.duty_u16(0)  # 原 duty(0) -> duty_u16(0)
        self._state = False

    def toggle(self) -> None:
        """
        切换 UV 矩阵状态（开/关）。
        Notes:
            根据当前状态调用 on() 或 off()。

        ==========================================

        Toggle UV matrix state.
        Notes:
            Calls on() if currently OFF, or off() if currently ON.
        """
        if self._state:
            self.off()
        else:
            self.on()

    def set_brightness(self, duty: int) -> None:
        """
        设置 UV 矩阵亮度。

        Args:
            duty (int): PWM 占空比，范围 0–1023。

        Raises:
            ValueError: duty 超出 0-1023 范围。

        Notes:
            调用此方法不会改变 _state 状态，只调节亮度。

        ==========================================

        Set UV matrix brightness.

        Args:
            duty (int): PWM duty cycle, range 0–1023.

        Raises:
            ValueError: If duty is outside 0-1023.

        Notes:
            Does not change _state, only adjusts brightness.
        """
        if not (0 <= duty <= 512):
            raise ValueError("PWM duty must be 0-512")
            # 转换 0-1023 到 0-65535
        self._pwm.duty_u16(int(duty * 65535 / 1023))

    def get_state(self) -> bool:
        """
        获取 UV 矩阵当前状态。
        Returns:
            bool: True 表示亮，False 表示灭。
        ==========================================

        Get current state of UV matrix.
        Returns:
            bool: True=ON, False=OFF.

        """
        return self._state

    @property
    def digital(self) -> Pin:
        """
        返回绑定的 MOSFET 控制引脚对象。

        Returns:
            Pin: MOSFET 控制引脚对象。

        ==========================================

        Return the control Pin object.

        Returns:
            Pin: MOSFET control Pin.

        """
        return self._digital

    @property
    def pwm(self) -> PWM:
        """
        返回绑定的 PWM 对象。

        Returns:
            PWM: PWM 对象，用于亮度调节。

        ==========================================

        Return the PWM object for brightness control.

        Returns:
            PWM: PWM object.

        """
        return self._pwm

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
