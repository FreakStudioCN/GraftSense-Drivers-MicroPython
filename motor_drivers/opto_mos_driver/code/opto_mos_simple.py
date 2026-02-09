# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/22 上午9:42
# @Author  : 缪贵成
# @File    : opto_mos_simple.py
# @Description :opto_mos_simple驱动文件
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

class OptoMosSimple:
    """
    该类控制光耦+MOS 管电路，基于 PWM 输出占空比来驱动负载，支持直接 duty/百分比设置。
    仅接受已创建的 PWM 对象，不在类内部创建 PWM。

    Attributes:
        pwm (PWM): machine.PWM 实例，用于生成 PWM 信号。
        pwm_max (int): PWM 最大计数范围（例如 65535 或 1023）。
        inverted (bool): 是否反向输出，占空比翻转。
        _duty (int): 当前占空比（计数值）。

    Methods:
        init() -> None: 初始化输出，默认关闭（0% 占空比）。
        set_duty(duty: int) -> None: 设置占空比（计数值，范围 0..pwm_max）。
        set_percent(percent: float) -> None: 设置占空比百分比（0.0..100.0）。
        full_on() -> None: 置为全速（100% 占空比）。
        off() -> None: 关闭输出（0% 占空比）。
        get_status() -> dict: 返回当前状态字典。
        deinit() -> None: 释放或复位 PWM 资源。

    Notes:
        duty 与 percent 超出范围会自动裁剪。
        inverted=True 时，占空比逻辑取反。
        本类仅封装 PWM duty，不修改 PWM 频率。

    ==========================================

    OptoMosSimple driver for controlling an optocoupler + MOS circuit using PWM.
    Accepts an already created PWM object only.

    Attributes:
        pwm (PWM): machine.PWM instance.
        pwm_max (int): PWM counter max (e.g., 65535 or 1023).
        inverted (bool): whether duty is inverted.
        _duty (int): current duty count value.

    Notes:
        Duty/percent values are clamped to valid range.
        inverted=True inverts the duty cycle logic.
        Only duty is controlled, not PWM frequency.
    """

    def __init__(self, pwm: "PWM", pwm_max: int = 65535, inverted: bool = False) -> None:
        """
        构造函数，初始化 PWM 控制对象。
        必须传入已创建的 PWM 对象。·

        Args:
            pwm (PWM): 已初始化的 PWM 对象。
            pwm_max (int): PWM 最大计数，默认 65535。
            inverted (bool): 是否反向输出，默认 False。

        Raises:
            ValueError: 当 pwm 未提供时。

        Notes:
            仅保存 PWM 对象引用，不改变其频率。

        ==========================================

        Constructor. Pass in an initialized PWM object.

        Args:
            pwm (PWM): Initialized PWM object.
            pwm_max (int): Maximum PWM counter (default 65535).
            inverted (bool): Invert duty output (default False).

        Raises:
            ValueError: If PWM object is not provided.

        Notes:
            Stores PWM reference; does not change frequency.
        """
        if pwm is None:
            raise ValueError("PWM object must be provided")
        self.pwm = pwm
        self.pwm_max = pwm_max
        self.inverted = inverted
        self._duty = 0

    def init(self) -> None:
        """
        初始化输出，占空比置为 0%。

        Notes:
            幂等，可重复调用。
            相当于 set_duty(0)。

        ==========================================

        Initialize output, sets duty to 0%.

        Notes:
            Idempotent, safe to call multiple times.
            Equivalent to set_duty(0).
        """
        self.set_duty(0)

    def set_duty(self, duty: int) -> None:
        """
        设置占空比（计数值），超范围自动裁剪。
        Args:
            duty (int): 占空比计数值，范围 0..pwm_max。

        Raises:
            ValueError: duty 小于 0 或大于 pwm_max 时被裁剪，不会报错。

        Notes:
            inverted=True 时，实际输出为反向占空比。
            内部会调用 pwm.duty_u16() 设置 PWM。

        ==========================================

        Set duty in counter value, clamped to 0..pwm_max.

        Args:
            duty (int): Duty count value (0..pwm_max).

        Raises:
            ValueError: Out-of-range duty is clamped, no error thrown.

        Notes:
            If inverted=True, duty is inverted internally.
            Calls pwm.duty_u16() to set PWM.
        """

        # 占空比剪裁函数，限制在0-65535之内
        duty = max(0, min(duty, self.pwm_max))
        if self.inverted:
            # 占空比反向
            duty = self.pwm_max - duty
        self._duty = duty
        self.pwm.duty_u16(duty)

    def set_percent(self, percent: float) -> None:
        """
        设置占空比百分比，超范围自动裁剪。
        Args:
            percent (float): 占空比百分比，范围 0.0..100.0。

        Raises:
            ValueError: 输入超出范围时被裁剪，不会报错。

        Notes:
            内部会转换为 duty 计数值并调用 set_duty。
            inverted 属性会影响实际输出。

        ==========================================

        Set duty cycle as percentage, clamped to 0.0..100.0.

        Args:
            percent (float): Duty percentage (0.0..100.0).

        Raises:
            ValueError: Out-of-range percent is clamped, no error thrown.

        Notes:
            Internally converted to duty count and calls set_duty.
            inverted property affects output.
        """
        percent = max(0.0, min(percent, 100.0))
        duty = int(percent / 100.0 * self.pwm_max)
        self.set_duty(duty)

    def full_on(self) -> None:
        """
        设置为全速（100% 占空比）。

        Notes:
            相当于 set_duty(pwm_max)。

        ==========================================

        Set full speed (100% duty).

        Notes:
            Equivalent to set_duty(pwm_max).
        """
        self.set_duty(self.pwm_max)

    def off(self) -> None:
        """
        关闭输出（0% 占空比）。

        Notes:
            相当于 set_duty(0)。

        ==========================================

        Turn off output (0% duty).

        Notes:
            Equivalent to set_duty(0).
        """
        self.set_duty(0)

    def get_status(self) -> dict:
        """
        获取当前状态字典。

        Returns:
            dict:
                {
                    "duty": int,        # 当前占空比计数值
                    "percent": float,   # 当前占空比百分比
                    "pwm_max": int,     # PWM 最大计数
                    "inverted": bool    # 是否反向输出
                }

        Notes:
            返回的 percent 已考虑 inverted 逻辑。

        ==========================================

        Get current status.
        Returns:
            dict:
                {
                    "duty": int,        # current duty value
                    "percent": float,   # current duty percentage
                    "pwm_max": int,     # PWM max counter
                    "inverted": bool    # inverted flag
                }

        Notes:
            Percent reflects inverted output.
        """
        percent = (self._duty / self.pwm_max) * 100.0
        return {
            "duty": self._duty,
            "percent": percent,
            "pwm_max": self.pwm_max,
            "inverted": self.inverted,
        }

    def deinit(self) -> None:
        """
        释放或复位 PWM 资源。

        Notes:
            如果平台支持 pwm.deinit()，则调用。
            否则将输出 duty 置为 0。

        ==========================================

        Release or reset PWM resource.

        Notes:
            Calls pwm.deinit() if supported.
            Otherwise sets duty to 0.
        """
        try:
            self.pwm.deinit()
        except AttributeError:
            self.set_duty(0)

# ======================================== 初始化配置 ============================================

# ======================================== 主程序 ===============================================
