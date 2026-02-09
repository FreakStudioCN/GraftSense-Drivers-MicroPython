# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/28 上午11:22
# @Author  : 缪贵成
# @File    : fan_pwm.py
# @Description : pwm驱动散热风扇驱动文件
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

class FanPWM:
    """
    该类控制散热风扇的 PWM 输出，提供风扇开关和转速调节功能。

    Attributes:
        _pin (Pin): PWM 控制引脚对象。
        _pwm (PWM): machine.PWM 实例，用于输出 PWM 信号。
        _duty (int): 当前 PWM 占空比（0–1023）。

    Methods:
        __init__(pin: int, pwm_freq: int = 25000) -> None: 初始化风扇控制。
        on() -> None: 打开风扇（全速）。
        off() -> None: 关闭风扇。
        set_speed(duty: int) -> None: 设置风扇转速，占空比 0–1023。
        get_speed() -> int: 获取当前风扇占空比。
        digital() -> Pin: 返回绑定的 PWM 控制引脚对象。
        pwm() -> PWM: 返回 PWM 对象，可直接操作占空比或停止 PWM。

    Notes:
        duty=0 表示关闭风扇，duty=1023 表示全速。
        默认 PWM 频率 25kHz，低频可能会产生可闻噪音。
        不要在 ISR 中直接调用 set_speed 等会操作 PWM 的方法（ISR-unsafe）。

    ==========================================

    FanPWM driver for controlling a cooling fan via PWM.

    Attributes:
        _pin (Pin): PWM control pin object.
        _pwm (PWM): machine.PWM instance for PWM output.
        _duty (int): Current PWM duty cycle (0–1023).

    Methods:
        __init__(pin: int, pwm_freq: int = 25000) -> None: Initialize fan control.
        on() -> None: Turn fan ON (full speed).
        off() -> None: Turn fan OFF.
        set_speed(duty: int) -> None: Set fan speed (duty cycle 0–1023).
        get_speed() -> int: Get current duty cycle.
        digital() -> Pin: Return bound PWM control pin object.
        pwm() -> PWM: Return PWM object for direct control.

    Notes:
        duty=0 means OFF, duty=1023 means full speed.
        Default PWM frequency is 25kHz; lower frequencies may produce audible noise.
        Do not call set_speed or other PWM-modifying methods directly from ISR (not ISR-safe).
    """

    def __init__(self, pin: int, pwm_freq: int = 25000) -> None:
        """
        初始化风扇 PWM 控制。

        Args:
            pin (int): GPIO 引脚编号，用于连接风扇 PWM 控制端。
            pwm_freq (int, optional): PWM 频率，单位 Hz，默认 25000Hz。

        Raises:
            ValueError: 当 PWM 频率不在可接受范围时。
            RuntimeError: 初始化 PWM 失败时。

        Notes:
            PWM 频率过低会导致风扇产生可闻噪音。
            duty 范围限制为 0–1023。
            不要在 ISR 中直接调用（ISR-unsafe）。

        ==========================================

        Initialize fan PWM control.

        Args:
            pin (int): GPIO pin number connected to fan PWM control.
            pwm_freq (int, optional): PWM frequency in Hz, default 25000Hz.

        Raises:
            ValueError: If PWM frequency out of range.
            RuntimeError: If PWM initialization fails.

        Notes:
            Low PWM frequency may produce audible noise.
            Duty range: 0–1023.
            Not ISR-safe.
        """
        self._pin = Pin(pin, Pin.OUT)
        self._pwm = PWM(self._pin)
        self._pwm.freq(pwm_freq)
        self._duty = 0
        self._pwm.duty_u16(0)

    def on(self) -> None:
        """
        打开风扇，全速运行。

        Notes:
            等效于 set_speed(1023)，不建议在 ISR 中调用。

        ==========================================

        Turn fan ON (full speed).

        Notes:
            Equivalent to set_speed(1023), not ISR-safe.
        """
        self.set_speed(1023)

    def off(self) -> None:
        """
        关闭风扇。

        Notes:
            等效于 set_speed(0)，不建议在 ISR 中调用。

        ==========================================

        Turn fan OFF.

        Notes:
            Equivalent to set_speed(0), not ISR-safe.
        """
        self.set_speed(0)

    def set_speed(self, duty: int) -> None:
        """
        设置风扇转速。

        Args:
            duty (int): 占空比，范围 0–1023。

        Notes:
            duty=0 表示关闭，duty=1023 表示全速。
            内部会映射到 16 位 PWM。
            不建议在 ISR 中调用。

        ==========================================

        Set fan speed.

        Args:
            duty (int): Duty cycle, 0–1023.

        Notes:
            duty=0 means OFF, duty=1023 means full speed.
            Mapped internally to 16-bit PWM.
            Not ISR-safe.
        """
        duty = max(0, min(1023, duty))
        self._duty = duty
        self._pwm.duty_u16(int(duty / 1023 * 65535))

    def get_speed(self) -> int:
        """
        获取当前风扇占空比。

        Returns:
            int: 当前占空比（0–1023）。

        Notes:
            仅返回软件记录的值，不会读取硬件寄存器。

        ==========================================

        Get current fan duty cycle.

        Returns:
            int: Current duty (0–1023).

        Note:
            Only returns software-stored value, does not read hardware.
        """
        return self._duty

    @property
    def digital(self) -> "Pin":
        """
        返回绑定的 PWM 控制引脚对象。

        Returns:
            Pin: PWM 控制引脚对象。

        Notes:
            可用于直接操作引脚，如高低电平控制。

        ==========================================

        Return bound PWM control pin.

        Returns:
            Pin: PWM control pin object.

        Notes:
            Can be used to directly manipulate pin output.
        """
        return self._pin

    @property
    def pwm(self) -> "PWM":
        """
        返回 PWM 对象。

        Returns:
            PWM: PWM 对象，可直接操作占空比或停止。

        Notes:
            可用于高级操作，不建议在 ISR 中直接调用。

        ==========================================

        Return PWM object.

        Returns:
            PWM: PWM object for direct control.

        Notes:
            Not ISR-safe for direct calls.
        """
        return self._pwm

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
