# Python env   : MicroPython v1.29.0 / ESP32-C3
# -*- coding: utf-8 -*-
# @Time    : 2026/11/06
# @Author  : 赵岩松
# @File    : encoder.py
# @Description : AB 编码器单边沿计数与 RPM 换算
# @License : MIT

__version__ = "1.1.0"
__author__ = "赵岩松"
__license__ = "MIT"
__platform__ = "MicroPython v1.29.0 / ESP32-C3"

# MG310P20 Hall AB Encoder Driver
#
# ESP32-C3 MicroPython
#
# Encoder:
#
# A -> GPIO5
# B -> GPIO6
#
#
# Motor:
#
# MG310P20_7.4V
#
# PPR:
#     13
#
# Gear Ratio:
#     20
#
#
# Counting:
#
# A rising edge
#
# Count per output revolution:
#
# 13 * 20 = 260

# ======================================== 导入相关模块 ========================================

import math

from machine import Pin, disable_irq, enable_irq
from micropython import alloc_emergency_exception_buf

# 为中断异常诊断预留空间；不改变软 IRQ 的计数和相位采样顺序。
alloc_emergency_exception_buf(100)

# ======================================== 全局变量 ========================================

# ======================================== 功能函数 ========================================

# ======================================== 自定义类 ========================================


class Encoder:
    """AB 编码器 A 相上升沿计数器。

    ==================
    AB encoder counter using A rising edges.

    Attributes:
        count 为累计计数；direction 为末次方向；count_per_rev 为输出轴每圈计数。 / Signed count, last direction and counts per output revolution.
    Methods:
        get_count、get_direction、reset、get_rpm、deinit。
    Notes:
        默认 13×20=260 次/输出轴圈，非四倍频。 / Default resolution is 260, not quadrature x4.
    """

    def __init__(self, pin_a: int, pin_b: int, ppr: int = 13, gear_ratio: float = 20) -> None:
        """校验配置并创建实例。

        ==================
        Validate configuration and initialize the instance.

        Args:
            pin_a: 编码器 A 相 GPIO 编号 / Encoder A GPIO number.
            pin_b: 编码器 B 相 GPIO 编号 / Encoder B GPIO number.
            ppr: A 相上升沿计数时电机轴每圈脉冲数 / A-rising counts per motor revolution.
            gear_ratio: 电机轴到输出轴减速比 / Motor-to-output reduction ratio.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception.

        Notes:
            创建 GPIO 并注册 A 相 IRQ / Create GPIO and register A-rising IRQ.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if type(pin_a) is not int or type(pin_b) is not int or min(pin_a, pin_b) < 0 or pin_a == pin_b:
            raise ValueError("Encoder GPIO numbers must be distinct nonnegative integers")
        if type(ppr) is not int or type(gear_ratio) not in (int, float) or not math.isfinite(gear_ratio):
            raise ValueError("Encoder resolution must be integer and gear ratio finite")
        if ppr <= 0 or gear_ratio <= 0:
            raise ValueError("Encoder resolution and gear ratio must be positive")
        self.pin_a = Pin(pin_a, Pin.IN, Pin.PULL_UP)

        self.pin_b = Pin(pin_b, Pin.IN, Pin.PULL_UP)

        self.count = 0

        self.direction = 0

        self.count_per_rev = ppr * gear_ratio

        self.pin_a.irq(trigger=Pin.IRQ_RISING, handler=self._irq)

    def get_count(self) -> int:
        """读取累计有符号计数。

        ==================
        Read the accumulated signed count.

        Args:
            无 / None.

        Returns:
            int：计数、方向或应用值，含义见上述说明 / Count, direction or applied value.

        Raises:
            无主动抛出；不访问 I/O / No explicit exceptions; no I/O.

        Notes:
            仅读取状态；不写硬件 / Read state only; no hardware writes.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """

        state = disable_irq()
        try:
            return self.count
        finally:
            enable_irq(state)

    def get_direction(self) -> int:
        """读取最后一个脉冲方向：-1、0 或 1。

        ==================
        Read the last pulse direction: -1, 0 or 1.

        Args:
            无 / None.

        Returns:
            int：计数、方向或应用值，含义见上述说明 / Count, direction or applied value.

        Raises:
            无主动抛出；不访问 I/O / No explicit exceptions; no I/O.

        Notes:
            仅读取状态；不写硬件 / Read state only; no hardware writes.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """

        state = disable_irq()
        try:
            return self.direction
        finally:
            enable_irq(state)

    def reset(self) -> None:
        """在 IRQ 临界区内清零计数及方向。

        ==================
        Clear count and direction in an IRQ critical section.

        Args:
            无 / None.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception.

        Notes:
            保护并修改计数状态；不写电机输出 / Protect and modify count state.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """

        # 清零共享字段时保护临界区，避免脉冲在两次赋值间插入。
        state = disable_irq()
        try:
            self.count = 0
            self.direction = 0
        finally:
            enable_irq(state)

    def get_rpm(self, delta_count: int, dt: float) -> float:
        """按 A 相上升沿分辨率与实测周期换算 RPM。

        ==================
        Convert the count difference and elapsed seconds to signed RPM.

        Args:
            delta_count: 采样周期内有符号脉冲增量 / Signed count difference over the interval.
            dt: 采样周期秒数；<=0 返回零 / Elapsed seconds; nonpositive returns zero.

        Returns:
            float：有符号输出轴 RPM；dt<=0 返回 0 / Signed output RPM; zero for dt<=0.

        Raises:
            无主动抛出；不访问 I/O / No explicit exceptions; no I/O.

        Notes:
            仅读取状态；不写硬件 / Read state only; no hardware writes.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if type(delta_count) is not int:
            raise ValueError("delta_count must be an integer")
        if type(dt) not in (int, float) or not math.isfinite(dt):
            raise ValueError("dt must be finite")

        if dt <= 0:

            return 0

        rpm = delta_count / self.count_per_rev * 60 / dt

        return rpm

    def _irq(self, pin: object) -> None:
        """
        A相上升沿触发

        根据B相判断方向

        注意：
        这里保持之前Phase1验证通过的方向
        """

        if self.pin_b.value():

            self.count -= 1

            self.direction = -1

        else:

            self.count += 1

            self.direction = 1

    def deinit(self) -> None:
        """注销本实例编码器 IRQ。

        ==================
        Detach this instance encoder IRQ.

        Args:
            无 / None.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception.

        Notes:
            注销 A 相 IRQ；不改变 PWM 输出 / Detach A IRQ without changing PWM.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        self.pin_a.irq(handler=None)


# ======================================== 初始化配置 ========================================

# ======================================== 主程序 ========================================
