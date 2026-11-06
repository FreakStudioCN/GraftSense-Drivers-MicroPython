# Python env   : MicroPython v1.29.0 / ESP32-C3
# -*- coding: utf-8 -*-
# @Time    : 2026/11/06
# @Author  : 赵岩松
# @File    : pid.py
# @Description : 独立 PID 速度控制器
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


class PID:
    """可独立复用的离散 PID 控制器。

    ==================
    Reusable discrete PID controller.

    Attributes:
        kp、ki、kd、target、dt 及 integral、output 保存配置与状态 / Gains, target, seconds and internal state.
    Methods:
        update、set_target、set_params、set_enabled、reset、deinit。
    Notes:
        默认停用；积分限幅限制乘 Ki 前状态；不访问硬件。 / Disabled initially; integral bounds apply before Ki; no hardware access.
    """

    def __init__(
        self,
        kp: float = 0.0,
        ki: float = 0.0,
        kd: float = 0.0,
        target: float = 0.0,
        dt: float = 0.05,
        output_limit: tuple = (-100, 100),
        integral_limit: tuple = (-100, 100),
    ) -> None:
        """校验配置并创建实例。

        ==================
        Validate configuration and initialize the instance.

        Args:
            kp: 比例增益；setter 中 None 保留原值 / Proportional gain; None keeps old value.
            ki: 积分增益；setter 中 None 保留原值 / Integral gain; None keeps old value.
            kd: 微分增益；setter 中 None 保留原值 / Derivative gain; None keeps old value.
            target: 目标值，与 feedback 同单位 / Target in the feedback unit.
            dt: 时间间隔，秒；update 中 None 使用实例默认值 / Seconds; None uses default.
            output_limit: 输出下限、上限，PWM 百分比 / Output bounds in PWM percent.
            integral_limit: 积分状态下限、上限；尚未乘 Ki / Integral-state bounds before Ki.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError：非有限值或配置无效；TypeError：参数类型无效。 / Non-finite values, invalid configuration or argument types.

        Notes:
            修改 PID 内部状态；不访问硬件 / Modify PID state only.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
            不创建硬件；默认 enabled=False / No hardware; initially disabled.
        """
        for value in (kp, ki, kd, target, dt):
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError("PID values must be finite")
        for bounds in (output_limit, integral_limit):
            if not isinstance(bounds, (tuple, list)) or len(bounds) != 2:
                raise ValueError("Limits must be a lower and upper pair")
            if any(type(value) not in (int, float) or not math.isfinite(value) for value in bounds):
                raise ValueError("Limits must be finite")
        if dt <= 0:
            raise ValueError("Control interval must be positive")
        if len(output_limit) != 2 or output_limit[0] > output_limit[1]:
            raise ValueError("Invalid output limits")
        if len(integral_limit) != 2 or integral_limit[0] > integral_limit[1]:
            raise ValueError("Invalid integral limits")
        self.kp = kp
        self.ki = ki
        self.kd = kd

        self.target = target

        self.dt = dt

        self.output_min = output_limit[0]
        self.output_max = output_limit[1]

        self.integral_min = integral_limit[0]
        self.integral_max = integral_limit[1]

        self.last_error = 0

        self.integral = 0

        self.output = 0

        # 安全启动位：默认禁止电机输出，必须显式 START=1 才闭环运行。
        self.enabled = False

    def update(self, feedback: float, dt: float = None, global_enabled: bool = True) -> float:
        """计算限幅 PID 输出；停用时清状态，dt<=0 时保留上次输出。

        ==================
        Calculate bounded PID output; disabled resets, dt<=0 retains output.

        Args:
            feedback: 当前实测值，电机应用使用 RPM / Measured feedback, RPM for motors.
            dt: 时间间隔，秒；update 中 None 使用实例默认值 / Seconds; None uses default.
            global_enabled: 总使能位；False 清状态并输出零 / Global enable; False resets output.

        Returns:
            float：限幅后的 PID 输出，电机应用单位为 PWM 百分比 / Bounded PWM percent.

        Raises:
            ValueError：非有限值或配置无效；TypeError：参数类型无效。 / Non-finite values, invalid configuration or argument types.

        Notes:
            修改 PID 内部状态；不访问硬件 / Modify PID state only.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if type(feedback) not in (int, float) or not math.isfinite(feedback):
            raise ValueError("feedback must be finite")
        if dt is not None and (type(dt) not in (int, float) or not math.isfinite(dt)):
            raise ValueError("dt must be finite or None")

        # ``self.enabled`` 是本电机启动位；global_enabled 是总启动位。
        if not self.enabled or not global_enabled:
            # 停止时清除旧积分，避免再次启动瞬间输出过大。
            self.reset()
            return 0

        if dt is None:
            dt = self.dt

        if dt <= 0:
            return self.output

        error = self.target - feedback

        # P
        p = self.kp * error

        # I
        self.integral += error * dt

        if self.integral > self.integral_max:
            self.integral = self.integral_max

        elif self.integral < self.integral_min:
            self.integral = self.integral_min

        i = self.ki * self.integral

        # D
        derivative = (error - self.last_error) / dt

        d = self.kd * derivative

        output = p + i + d

        # 输出限制

        if output > self.output_max:

            output = self.output_max

        elif output < self.output_min:

            output = self.output_min

        self.last_error = error

        self.output = output

        return output

    def set_target(self, target: float) -> None:
        """修改目标值，不自动使能。

        ==================
        Change the target without enabling output.

        Args:
            target: 目标值，与 feedback 同单位 / Target in the feedback unit.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError：非有限值或配置无效；TypeError：参数类型无效。 / Non-finite values, invalid configuration or argument types.

        Notes:
            修改 PID 内部状态；不访问硬件 / Modify PID state only.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if type(target) not in (int, float) or not math.isfinite(target):
            raise ValueError("target must be finite")

        self.target = target

    def set_params(self, kp: float = None, ki: float = None, kd: float = None) -> None:
        """在线修改增益；None 保留原值，不清除积分。

        ==================
        Change supplied gains without clearing the integral state.

        Args:
            kp: 比例增益；setter 中 None 保留原值 / Proportional gain; None keeps old value.
            ki: 积分增益；setter 中 None 保留原值 / Integral gain; None keeps old value.
            kd: 微分增益；setter 中 None 保留原值 / Derivative gain; None keeps old value.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError：非有限值或配置无效；TypeError：参数类型无效。 / Non-finite values, invalid configuration or argument types.

        Notes:
            修改 PID 内部状态；不访问硬件 / Modify PID state only.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        for value in (kp, ki, kd):
            if value is not None and (type(value) not in (int, float) or not math.isfinite(value)):
                raise ValueError("PID gains must be finite or None")

        if kp is not None:
            self.kp = kp

        if ki is not None:
            self.ki = ki

        if kd is not None:
            self.kd = kd

    def set_enabled(self, enabled: bool) -> None:
        """转换并设置使能位，禁用时清除积分和输出状态。

        ==================
        Set the enable flag; disabling resets integral and output state.

        Args:
            enabled: 使能位，按 bool 转换；禁用时清状态 / Enable flag converted with bool().

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError：非有限值或配置无效；TypeError：参数类型无效。 / Non-finite values, invalid configuration or argument types.

        Notes:
            修改 PID 内部状态；不访问硬件 / Modify PID state only.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if enabled is None or not isinstance(enabled, (bool, int)):
            raise ValueError("enabled must be bool or integer")

        self.enabled = bool(enabled)

        if not self.enabled:
            self.reset()

    def reset(self) -> None:
        """清除积分、历史误差和输出，保留目标与使能。

        ==================
        Clear integral, previous error and output; retain target and enable.

        Args:
            无 / None.

        Returns:
            None：无返回值 / No return value.

        Raises:
            无主动抛出；不访问 I/O / No explicit exceptions; no I/O.

        Notes:
            修改 PID 内部状态；不访问硬件 / Modify PID state only.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """

        self.last_error = 0

        self.integral = 0

        self.output = 0

    def deinit(self) -> None:
        """禁用 PID 并清除动态状态。

        ==================
        Disable PID and clear its dynamic state.

        Args:
            无 / None.
        Returns:
            None.
        Raises:
            无 / None.
        Notes:
            不访问硬件，保留目标和增益；不在 ISR 调用 / Not ISR-safe.
        """
        self.set_enabled(False)


# ======================================== 初始化配置 ========================================

# ======================================== 主程序 ========================================
