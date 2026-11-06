# Python env   : MicroPython v1.29.0 / ESP32-C3
# -*- coding: utf-8 -*-
# @Time    : 2026/11/06
# @Author  : 赵岩松
# @File    : motor_controller.py
# @Description : 多电机独立速度闭环与遥测
# @License : MIT

__version__ = "1.1.0"
__author__ = "赵岩松"
__license__ = "MIT"
__platform__ = "MicroPython v1.29.0 / ESP32-C3"

# Independent encoder motor loops. Call update() regularly from the application.
#
# Motor IDs are 1-based, in the order of motor_configs. Setting a target does
# not start a motor: call start_motor()/start_all() explicitly.

# ======================================== 导入相关模块 ========================================

import time
import math
from motor import DCMotor
from encoder import Encoder
from pid import PID

# ======================================== 全局变量 ========================================

# ======================================== 功能函数 ========================================

# ======================================== 自定义类 ========================================


class MotorController:
    """按 ID 管理独立编码器速度闭环。

    ==================
    Manage independent encoder speed loops by motor ID.

    Attributes:
        _motors、_encoders、_pids 为本控制器管理的对象 / Managed motor, encoder and PID instances.
    Methods:
        set_target_rpm、set_pid、start_all、update、get_telemetry、deinit。
    Notes:
        配置项为 (PWM_A,PWM_B,GPIO_A,GPIO_B)，ID 从 1 开始；不创建后台任务。 / Config entries map channels and GPIO; IDs start at 1; no background task.
    """

    def __init__(
        self,
        pca: object,
        motor_configs: object,
        pid_params: object,
        target_rpms: object = None,
        ppr: int = 13,
        gear_ratio: float = 20,
        output_limit: tuple = (-100, 100),
        integral_limit: tuple = (-50, 50),
    ) -> None:
        """校验配置并创建实例。

        ==================
        Validate configuration and initialize the instance.

        Args:
            pca: 调用方提供、实现 duty() 的对象 / Caller-owned PWM driver.
            motor_configs: 每项 (PWM_A, PWM_B, GPIO_A, GPIO_B) / Channel and encoder pin tuples.
            pid_params: 按 ID 排列的 (Kp, Ki, Kd) / Gain triples in motor-ID order.
            target_rpms: 初始目标 RPM 序列，None 表示全部为零 / Initial RPM targets or None.
            ppr: A 相上升沿计数时电机轴每圈脉冲数 / A-rising counts per motor revolution.
            gear_ratio: 电机轴到输出轴减速比 / Motor-to-output reduction ratio.
            output_limit: 输出下限、上限，PWM 百分比 / Output bounds in PWM percent.
            integral_limit: 积分状态下限、上限；尚未乘 Ki / Integral-state bounds before Ki.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if not hasattr(pca, "duty"):
            raise ValueError("pca must provide duty()")
        if not isinstance(motor_configs, (tuple, list)) or not isinstance(pid_params, (tuple, list)):
            raise ValueError("Motor and PID configurations must be sequences")
        for config in motor_configs:
            if not isinstance(config, (tuple, list)) or len(config) != 4:
                raise ValueError("Motor configuration must contain two channels and two GPIOs")
        for params in pid_params:
            if not isinstance(params, (tuple, list)) or len(params) != 3:
                raise ValueError("PID configuration must contain three gains")
        count = len(motor_configs)
        if not count or len(pid_params) != count:
            raise ValueError("Motor and PID configurations must match")
        if target_rpms is None:
            target_rpms = [0] * count
        if len(target_rpms) != count or ppr <= 0 or gear_ratio <= 0:
            raise ValueError("Invalid target or encoder configuration")
        self._motors = []
        self._encoders = []
        self._pids = []
        self._rpms = [0.0] * count
        self._pwms = [0.0] * count
        try:
            for config, params, target in zip(motor_configs, pid_params, target_rpms):
                a, b, enc_a, enc_b = config
                motor = DCMotor(pca, a, b)
                self._motors.append(motor)
                motor.stop()
                self._encoders.append(Encoder(enc_a, enc_b, ppr=ppr, gear_ratio=gear_ratio))
                kp, ki, kd = params
                self._pids.append(
                    PID(
                        kp,
                        ki,
                        kd,
                        target=target,
                        output_limit=output_limit,
                        integral_limit=integral_limit,
                    )
                )
        except BaseException:
            for motor in self._motors:
                try:
                    motor.stop()
                except Exception:
                    pass
            for encoder in self._encoders:
                try:
                    encoder.deinit()
                except Exception:
                    pass
            raise
        self._last_counts = [encoder.get_count() for encoder in self._encoders]
        self._last_time = time.ticks_ms()

    def set_target_rpm(self, motor_id: int, rpm: float) -> None:
        """设置带符号目标 RPM；不自动启动电机。

        ==================
        Set signed target RPM without starting the motor.

        Args:
            motor_id: 从 1 开始的电机 ID / One-based motor ID.
            rpm: 带符号目标转速 RPM / Signed target RPM.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if not isinstance(motor_id, int) or not 1 <= motor_id <= len(self._motors):
            raise ValueError("Invalid motor ID")
        self._pids[self._index(motor_id)].set_target(rpm)

    def set_target_rpms(self, rpms: object) -> None:
        """按 ID 顺序设置全部目标；不自动启动。

        ==================
        Set all targets in ID order without starting motors.

        Args:
            rpms: 按电机 ID 排列的目标 RPM 序列 / Target RPM sequence in ID order.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if len(rpms) != len(self._pids):
            raise ValueError("One target per motor is required")
        targets = tuple(rpms)
        if any(type(rpm) not in (int, float) or not math.isfinite(rpm) for rpm in targets):
            raise ValueError("Targets must be finite numbers")
        for pid, rpm in zip(self._pids, targets):
            pid.set_target(rpm)

    def set_pid(self, motor_id: int, kp: float = None, ki: float = None, kd: float = None) -> None:
        """在线修改指定电机增益，None 保留原值。

        ==================
        Change one motor gain set; None keeps the previous value.

        Args:
            motor_id: 从 1 开始的电机 ID / One-based motor ID.
            kp: 比例增益；setter 中 None 保留原值 / Proportional gain; None keeps old value.
            ki: 积分增益；setter 中 None 保留原值 / Integral gain; None keeps old value.
            kd: 微分增益；setter 中 None 保留原值 / Derivative gain; None keeps old value.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if not isinstance(motor_id, int) or not 1 <= motor_id <= len(self._motors):
            raise ValueError("Invalid motor ID")
        self._pids[self._index(motor_id)].set_params(kp, ki, kd)

    def start_motor(self, motor_id: int) -> None:
        """使能指定闭环，下次 update 更新输出。

        ==================
        Enable one loop for output on the next update.

        Args:
            motor_id: 从 1 开始的电机 ID / One-based motor ID.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if not isinstance(motor_id, int) or not 1 <= motor_id <= len(self._motors):
            raise ValueError("Invalid motor ID")
        self._pids[self._index(motor_id)].set_enabled(True)

    def start_all(self) -> None:
        """使能全部闭环，保留各自目标。

        ==================
        Enable all loops while retaining their targets.

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
        for pid in self._pids:
            pid.set_enabled(True)

    def stop_motor(self, motor_id: int) -> None:
        """禁用指定 PID 并立即停止该路输出，保留目标。

        ==================
        Disable one PID and stop its output; retain the target.

        Args:
            motor_id: 从 1 开始的电机 ID / One-based motor ID.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if not isinstance(motor_id, int) or not 1 <= motor_id <= len(self._motors):
            raise ValueError("Invalid motor ID")
        index = self._index(motor_id)
        self._pids[index].set_enabled(False)
        self._pwms[index] = 0
        self._motors[index].stop()

    def stop_all(self) -> None:
        """尝试停止全部电机；某路失败仍处理其他路，最后抛首个异常。

        ==================
        Attempt every motor stop and then raise the first failure.

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
        for motor_id in range(1, len(self._motors) + 1):
            try:
                self.stop_motor(motor_id)
            except Exception as exc:
                if error is None:
                    error = exc
        if error is not None:
            raise error

    def get_motor_rpm(self, motor_id: int) -> float:
        """读取最近一次更新得到的带符号 RPM。

        ==================
        Read signed RPM from the latest update.

        Args:
            motor_id: 从 1 开始的电机 ID / One-based motor ID.

        Returns:
            float：带符号的输出轴转速，RPM / Signed output-shaft speed in RPM.

        Raises:
            ValueError：电机编号无效 / Invalid motor ID; no I2C operation.

        Notes:
            仅读取状态；不写硬件 / Read state only; no hardware writes.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if not isinstance(motor_id, int) or not 1 <= motor_id <= len(self._motors):
            raise ValueError("Invalid motor ID")
        return self._rpms[self._index(motor_id)]

    def get_encoder_count(self, motor_id: int) -> int:
        """读取实时累计有符号脉冲计数。

        ==================
        Read the current signed accumulated pulse count.

        Args:
            motor_id: 从 1 开始的电机 ID / One-based motor ID.

        Returns:
            int：累计的有符号编码器脉冲数 / Accumulated signed encoder count.

        Raises:
            ValueError：电机编号无效 / Invalid motor ID; no I2C operation.

        Notes:
            仅读取状态；不写硬件 / Read state only; no hardware writes.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if not isinstance(motor_id, int) or not 1 <= motor_id <= len(self._motors):
            raise ValueError("Invalid motor ID")
        return self._encoders[self._index(motor_id)].get_count()

    def get_encoder_direction(self, motor_id: int) -> int:
        """读取最后一个脉冲的方向，停止后可能保持旧值。

        ==================
        Read the last pulse direction, which may persist after stopping.

        Args:
            motor_id: 从 1 开始的电机 ID / One-based motor ID.

        Returns:
            int：最后计数方向，-1/0/1 / Last count direction: -1, 0 or 1.

        Raises:
            ValueError：电机编号无效 / Invalid motor ID; no I2C operation.

        Notes:
            仅读取状态；不写硬件 / Read state only; no hardware writes.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if not isinstance(motor_id, int) or not 1 <= motor_id <= len(self._motors):
            raise ValueError("Invalid motor ID")
        return self._encoders[self._index(motor_id)].get_direction()

    def update(self, motor_ids: object = None) -> bool:
        """按实测 dt 更新速度闭环；选择 ID 仅限制输出，不限制反馈。

        ==================
        Update loops using measured dt; selection limits output writes only.

        Args:
            motor_ids: None 写全部输出；ID 序列仅写所选路，仍采集全部反馈 / Output selection.

        Returns:
            bool：本次完成更新为 True，未到周期或 dt<=0 为 False / True if updated.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if motor_ids is not None and not hasattr(motor_ids, "__iter__"):
            raise ValueError("motor_ids must be iterable or None")
        # 兼容层可只更新 PID 模式输出；仍采集全部编码器，避免开环测速中断。
        # 默认 None 保留原来四路全部更新的行为。
        selected = None
        if motor_ids is not None:
            selected = {self._index(motor_id) for motor_id in motor_ids}
        now = time.ticks_ms()
        # ticks_diff 处理 MicroPython 毫秒计时器回绕；dt 单位为秒。
        dt = time.ticks_diff(now, self._last_time) / 1000
        if dt <= 0:
            return False
        try:
            # 先采集所有计数，再执行 I2C 输出，减少各轮采样时间差。
            counts = [encoder.get_count() for encoder in self._encoders]
            for index, (motor, encoder, pid) in enumerate(zip(self._motors, self._encoders, self._pids)):
                rpm = encoder.get_rpm(counts[index] - self._last_counts[index], dt)
                self._rpms[index] = rpm
                if selected is None or index in selected:
                    pwm = pid.update(rpm, dt)
                    motor.set_speed(pwm)
                    self._pwms[index] = pwm
            self._last_counts = counts
            self._last_time = now
        except BaseException:
            try:
                self.stop_all()
            except Exception:
                pass
            raise
        return True

    def get_telemetry(self) -> list:
        """读取每路八字段及末尾全使能位的遥测快照。

        ==================
        Read eight fields per motor followed by the all-enabled flag.

        Args:
            无 / None.

        Returns:
            list：每路 target,RPM,PWM,error,Kp,Ki,Kd,enabled，末尾全使能位 / Telemetry snapshot.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception.

        Notes:
            仅读取状态；不写硬件 / Read state only; no hardware writes.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        data = []
        for index, pid in enumerate(self._pids):
            rpm = self._rpms[index]
            data.extend(
                (
                    pid.target,
                    rpm,
                    self._pwms[index],
                    pid.target - rpm,
                    pid.kp,
                    pid.ki,
                    pid.kd,
                    int(pid.enabled),
                )
            )
        data.append(int(all(pid.enabled for pid in self._pids)))
        return data

    def _index(self, motor_id: int) -> int:
        if not isinstance(motor_id, int) or not 1 <= motor_id <= len(self._motors):
            raise ValueError("Invalid motor ID")
        return motor_id - 1

    def deinit(self) -> None:
        """停止全部输出，并逐路注销本控制器创建的编码器 IRQ。

        ==================
        Stop all outputs and detach every encoder IRQ owned by this controller.

        Args:
            无 / None.
        Returns:
            None.
        Raises:
            Exception: 尝试全部清理后抛首个异常 / First error after all attempts.
        Notes:
            不关闭共享 PWM 驱动或 I2C；不在 ISR 调用 / Not ISR-safe.
        """
        error = None
        try:
            self.stop_all()
        except Exception as exc:
            error = exc
        for encoder in self._encoders:
            try:
                encoder.deinit()
            except Exception as exc:
                error = error or exc
        if error is not None:
            raise error


# ======================================== 初始化配置 ========================================

# ======================================== 主程序 ========================================
