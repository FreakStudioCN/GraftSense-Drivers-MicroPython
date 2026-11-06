# Python env   : MicroPython v1.29.0 / ESP32-C3
# -*- coding: utf-8 -*-
# @Time    : 2026/11/06
# @Author  : 赵岩松
# @File    : motor.py
# @Description : PCA9685 与 SS6285 电机百分比输出
# @License : MIT

__version__ = "1.1.0"
__author__ = "赵岩松"
__license__ = "MIT"
__platform__ = "MicroPython v1.29.0 / ESP32-C3"

# ======================================== 导入相关模块 ========================================

import math

# ======================================== 全局变量 ========================================

# ======================================== 功能函数 ========================================

# ======================================== 自定义类 ========================================


class DCMotor:
    """两个 PCA 通道控制一个直流电机。

    ==================
    Drive one DC motor through two PCA channels.

    Attributes:
        pca、channel_a、channel_b 为共享驱动和双输入通道 / PWM driver and input channels.
    Methods:
        set_speed、stop、deinit。
    Notes:
        速度为带符号百分比而非 RPM；不拥有共享 PCA 对象。 / Speed means PWM percent, not RPM; PCA is borrowed.
    """

    def __init__(self, pca: object, channel_a: int, channel_b: int) -> None:
        """校验配置并创建实例。

        ==================
        Validate configuration and initialize the instance.

        Args:
            pca: 调用方提供、实现 duty() 的对象 / Caller-owned PWM driver.
            channel_a: 电机输入 A 的 PCA 通道 0..15 / PCA channel for motor input A.
            channel_b: 电机输入 B 的 PCA 通道 0..15，与 A 不同 / Distinct channel for input B.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if type(channel_a) is not int or type(channel_b) is not int:
            raise ValueError("Motor channels must be integers")
        if not hasattr(pca, "duty"):
            raise TypeError("pca must provide duty()")
        if not (0 <= channel_a <= 15 and 0 <= channel_b <= 15) or channel_a == channel_b:
            raise ValueError("Motor channels must be distinct and in range 0..15")
        self.pca = pca

        self.channel_a = channel_a

        self.channel_b = channel_b

    def set_speed(self, speed: float) -> None:
        """将带符号 PWM 百分比限幅后写入双输入。

        ==================
        Clamp signed PWM percentage and write the two inputs.

        Args:
            speed: 带符号 PWM 百分比，限幅至 -100..100 / Signed PWM percent, clamped.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if type(speed) not in (int, float) or not math.isfinite(speed):
            raise ValueError("speed must be finite")
        speed = max(-100, min(100, speed))

        duty = int(abs(speed) * 4095 / 100)

        if speed > 0:

            # 正转

            self.pca.duty(self.channel_a, duty)

            self.pca.duty(self.channel_b, 0)

        elif speed < 0:

            # 反转

            self.pca.duty(self.channel_a, 0)

            self.pca.duty(self.channel_b, duty)

        else:

            self.stop()

    def stop(self) -> None:
        """将本电机两个 PWM 输入置零。

        ==================
        Set both inputs of this motor to zero.

        Args:
            无 / None.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """

        error = None
        for channel in (self.channel_a, self.channel_b):
            try:
                self.pca.duty(channel, 0)
            except Exception as exc:
                if error is None:
                    error = exc
        if error is not None:
            raise error

    def deinit(self) -> None:
        """停止本电机，保留共享 PWM 驱动。

        ==================
        Stop this motor while preserving the borrowed PWM driver.

        Args:
            无 / None.
        Returns:
            None.
        Raises:
            OSError: PWM 写入失败 / PWM write failed.
        Notes:
            将本电机双输入置零；不在 ISR 调用 / Not ISR-safe.
        """
        self.stop()


# ======================================== 初始化配置 ========================================

# ======================================== 主程序 ========================================
