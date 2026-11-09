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

# 独立编码器速度环，由应用持续调用update()。
# 电机ID从1开始，顺序与motor_configs一致；设置目标后须显式启动。

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
    """按ID管理独立编码器速度闭环。
    Attributes:
        _motors、_encoders、_pids：本对象管理的电机、编码器和PID。
    Methods:
        set_target_rpm、set_pid、start_all、update、get_faults、clear_faults、deinit。
    Notes:
        ID从1开始；update由主循环调用，不创建后台任务。
    ==================
    Manage independent encoder speed loops by motor ID.
    Attributes:
        _motors, _encoders, _pids: managed motors, encoders and PID instances.
    Methods:
        set_target_rpm, set_pid, start_all, update, get_faults, clear_faults, deinit.
    Notes:
        IDs start at one; the application calls update; no background task is created.
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
        feedback_protection: object = None,
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
            feedback_protection: None采用默认保护；dict覆盖配置；False显式禁用 / Defaults, configuration dict, or False to disable.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数类型、范围或结构无效 / Invalid argument type, range or structure.
            OSError：底层硬件操作失败，保持原异常 / Hardware operation failed; the original exception is retained.

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
        self._faults = [None] * count
        self._all_faulted = False
        self._guard_start = [None] * count
        self._guard_since = [None] * count
        self._guard_count = [0] * count
        self._guard_sign = [0] * count
        if feedback_protection is None or feedback_protection is True:
            feedback_protection = {}
        elif feedback_protection is False:
            feedback_protection = {"enabled": False}
        if not isinstance(feedback_protection, dict):
            raise ValueError("feedback_protection must be a dict, bool or None")
        self.configure_feedback_protection(**feedback_protection)
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
            ValueError/TypeError：参数类型、范围或结构无效 / Invalid argument type, range or structure.

        Notes:
            仅更新目标，不启动电机 / Update the target without starting a motor.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if not isinstance(motor_id, int) or not 1 <= motor_id <= len(self._motors):
            raise ValueError("Invalid motor ID")
        index = self._index(motor_id)
        pid = self._pids[index]
        old_sign = (pid.target > 0) - (pid.target < 0)
        pid.set_target(rpm)
        if (rpm > 0) - (rpm < 0) != old_sign:
            self._reset_guard(index)

    def set_target_rpms(self, rpms: object) -> None:
        """按 ID 顺序设置全部目标；不自动启动。

        ==================
        Set all targets in ID order without starting motors.

        Args:
            rpms: 按电机 ID 排列的目标 RPM 序列 / Target RPM sequence in ID order.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数类型、范围或结构无效 / Invalid argument type, range or structure.

        Notes:
            先验证整组目标，再赋值；不写PWM / Validate the entire group before assignment; no PWM writes.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if len(rpms) != len(self._pids):
            raise ValueError("One target per motor is required")
        targets = tuple(rpms)
        if any(type(rpm) not in (int, float) or not math.isfinite(rpm) for rpm in targets):
            raise ValueError("Targets must be finite numbers")
        for motor_id, rpm in enumerate(targets, 1):
            self.set_target_rpm(motor_id, rpm)

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
            ValueError/TypeError：参数类型、范围或结构无效 / Invalid argument type, range or structure.

        Notes:
            仅修改增益，不执行I2C操作 / Update gains only; no I2C operation.
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
            RuntimeError：保护故障锁存，须显式清除 / Protection fault is latched; explicit clearing is required.
            ValueError/TypeError：参数类型、范围或结构无效 / Invalid argument type, range or structure.

        Notes:
            仅启用对应PID，下次update才写PWM / Enable the PID; PWM is written by the next update.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if not isinstance(motor_id, int) or not 1 <= motor_id <= len(self._motors):
            raise ValueError("Invalid motor ID")
        index = self._index(motor_id)
        self._assert_can_drive(motor_id)
        if not self._pids[index].enabled:
            self._reset_guard(index)
            self._guard_start[index] = time.ticks_ms()
            self._guard_count[index] = self._encoders[index].get_count()
            target = self._pids[index].target
            self._guard_sign[index] = (target > 0) - (target < 0)
        self._pids[index].set_enabled(True)

    def start_all(self) -> None:
        """使能全部闭环，保留各自目标。

        ==================
        Enable all loops while retaining their targets.

        Args:
            无 / None.

        Returns:
            None：无返回值 / No return value.

        Raises:
            RuntimeError：保护故障锁存，须显式清除 / Protection fault is latched; explicit clearing is required.
            无主动抛出 / No explicit exceptions.

        Notes:
            仅启用所有PID，下次update才写PWM / Enable all PIDs; the next update writes PWM.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        # 先验证全部故障锁存，避免后一路拒绝启动时前一路已被使能。
        for motor_id in range(1, len(self._pids) + 1):
            self._assert_can_drive(motor_id)
        for motor_id in range(1, len(self._pids) + 1):
            self.start_motor(motor_id)

    def stop_motor(self, motor_id: int) -> None:
        """禁用指定 PID 并立即停止该路输出，保留目标。

        ==================
        Disable one PID and stop its output; retain the target.

        Args:
            motor_id: 从 1 开始的电机 ID / One-based motor ID.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数类型、范围或结构无效 / Invalid argument type, range or structure.
            OSError：底层硬件操作失败，保持原异常 / Hardware operation failed; the original exception is retained.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if not isinstance(motor_id, int) or not 1 <= motor_id <= len(self._motors):
            raise ValueError("Invalid motor ID")
        index = self._index(motor_id)
        self._pids[index].set_enabled(False)
        self._pwms[index] = 0
        self._reset_guard(index)
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
            Exception：尝试所有电机后传播首个停机异常 / First stop failure after all motor attempts.

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
            ValueError/TypeError：参数类型、范围或结构无效 / Invalid argument type, range or structure.

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
            ValueError/TypeError：参数类型、范围或结构无效 / Invalid argument type, range or structure.

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
            ValueError/TypeError：参数类型、范围或结构无效 / Invalid argument type, range or structure.

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
            bool：dt>0且完成本轮更新为True，否则为False / True when an update with positive dt completes.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        # 兼容层可只更新 PID 模式输出；仍采集全部编码器，避免开环测速中断。
        # 默认 None 保留原来四路全部更新的行为。
        selected = None
        if motor_ids is not None:
            # MicroPython内置列表可能没有可见的__iter__属性，直接验证迭代协议。
            motor_iterator = None
            try:
                motor_iterator = iter(motor_ids)
            except TypeError:
                pass
            if motor_iterator is None:
                raise ValueError("motor_ids must be iterable or None")
            # 全部消费并验证后才读取反馈或写输出；空集合保留只采样语义。
            selected = {self._index(motor_id) for motor_id in motor_iterator}
        now = time.ticks_ms()
        # ticks_diff 处理 MicroPython 毫秒计时器回绕；dt 单位为秒。
        dt = time.ticks_diff(now, self._last_time) / 1000
        if dt <= 0:
            return False
        try:
            # 先采集所有计数，再执行 I2C 输出，减少各轮采样时间差。
            counts = [encoder.get_count() for encoder in self._encoders]
            for index, encoder in enumerate(self._encoders):
                self._rpms[index] = encoder.get_rpm(counts[index] - self._last_counts[index], dt)
            # 故障停机写失败后，后续update仍重试关断，不隐式解除锁存。
            self._attempt_fault_stop()
            for index, (motor, pid) in enumerate(zip(self._motors, self._pids)):
                if self._all_faulted or self._faults[index] is not None:
                    continue
                if selected is None or index in selected:
                    pwm = pid.update(self._rpms[index], dt)
                    self._pwms[index] = pwm
                    if self._check_feedback(index, counts[index], now, pwm):
                        if self._all_faulted:
                            break
                        continue
                    motor.set_speed(pwm)
                else:
                    self._reset_guard(index)
            self._last_counts = counts
            self._last_time = now
        except BaseException:
            try:
                # I/O或其他更新异常仍按原有策略立即尝试全停，不被单路故障策略削弱。
                self._attempt_fault_stop(force_all=True)
            except Exception:
                pass
            raise
        return True

    def configure_feedback_protection(
        self, startup_grace_ms: int = 4000, timeout_ms: int = 2500, pwm_threshold: float = 25.0, stop_policy: str = "all", enabled: bool = True
    ) -> None:
        """配置无反馈保护，不清除故障或自动启动。
        ==================
        Configure no-feedback protection without clearing faults or starting motors.
        Args:
            startup_grace_ms: 启动/换向宽限毫秒数 / Startup and reversal grace in milliseconds.
            timeout_ms: 持续满足输出条件且无计数的超时 / Continuous driven no-count timeout in milliseconds.
            pwm_threshold: 启用检测的绝对PWM百分比阈值，严格大于 / Absolute PWM threshold, strictly exceeded.
            stop_policy: all停全部，motor只停故障路 / Stop all motors or only the faulted motor.
            enabled: 显式启用检测；禁用不清故障 / Enable detection; disabling does not clear faults.
        Returns:
            None：无返回值 / No return value.
        Raises:
            ValueError：配置类型、范围或策略错误 / Invalid configuration type, range or policy.
        Notes:
            重置检测计时；不写输出；仅随update执行，不保证断线物理关断 / Reset timing; no PWM write; detection runs in update only.
            默认值来自当前台架，需要按电机配置；非ISR-safe / Bench-derived defaults require application configuration; not ISR-safe.
        """
        limit = time.ticks_add(0, -1) // 2
        if type(startup_grace_ms) is not int or not 0 <= startup_grace_ms <= limit:
            raise ValueError("startup_grace_ms must fit the ticks_diff range")
        if type(timeout_ms) is not int or not 1 <= timeout_ms <= limit:
            raise ValueError("timeout_ms must be positive and fit the ticks_diff range")
        if type(pwm_threshold) not in (int, float) or not math.isfinite(pwm_threshold) or not 0 <= pwm_threshold < 100:
            raise ValueError("pwm_threshold must be finite and in range [0,100)")
        if stop_policy not in ("all", "motor"):
            raise ValueError("stop_policy must be all or motor")
        if type(enabled) is not bool:
            raise ValueError("enabled must be bool")
        self._feedback_protection = dict(
            startup_grace_ms=startup_grace_ms, timeout_ms=timeout_ms, pwm_threshold=pwm_threshold, stop_policy=stop_policy, enabled=enabled
        )
        for index in range(len(self._faults)):
            self._reset_guard(index)

    def get_feedback_protection(self) -> dict:
        """读取保护配置副本。
        ==================
        Read a copy of the feedback-protection configuration.
        Args:
            无 / None.
        Returns:
            dict：保护配置副本 / Configuration snapshot.
        Raises:
            无主动抛出 / No explicit exceptions.
        Notes:
            不修改状态或硬件；非ISR-safe / No state or hardware changes; not ISR-safe.
        """
        return dict(self._feedback_protection)

    def get_faults(self) -> tuple:
        """读取锁存故障及关断尝试结果。
        ==================
        Read latched faults and the result of shutdown attempts.
        Args:
            无 / None.
        Returns:
            tuple：故障字典副本，含ID、原因、时刻和停机写入状态 / Fault snapshots with ID, reason, time and stop-write status.
        Raises:
            无主动抛出 / No explicit exceptions.
        Notes:
            stop_writes_ok只表示写调用无异常，不是物理关断确认；非ISR-safe / Successful writes are not physical confirmation; not ISR-safe.
        """
        return tuple(dict(fault) for fault in self._faults if fault is not None)

    def clear_faults(self, motor_id: object = None) -> None:
        """先再次关断，再显式清除故障；保持PID禁用。
        ==================
        Attempt shutdown again, then clear faults explicitly while retaining disabled PIDs.
        Args:
            motor_id: 指定一路，None表示全部 / One motor ID, or None for all.
        Returns:
            None：无返回值 / No return value.
        Raises:
            ValueError：ID无效；Exception：关断失败，故障保留 / Invalid ID or failed shutdown; faults remain latched on failure.
        Notes:
            不启动电机；成功清除后仍须start；非ISR-safe / Does not start motors; explicit start is still required; not ISR-safe.
        """
        if motor_id is not None and (not isinstance(motor_id, int) or not 1 <= motor_id <= len(self._faults)):
            raise ValueError("Invalid motor ID")
        indices = range(len(self._faults)) if motor_id is None else (self._index(motor_id),)
        indices = [index for index in indices if self._faults[index] is not None]
        if not indices:
            return
        # 显式复位的关断尝试也计入状态；失败时不删除任何故障。
        for index, fault in enumerate(self._faults):
            if fault is not None and (self._all_faulted or index in indices):
                fault["stop_writes_ok"] = False
        try:
            self._attempt_fault_stop()
        except BaseException:
            try:
                self._attempt_fault_stop(force_all=True)
            except Exception:
                pass
            raise
        for index in indices:
            self._faults[index] = None
        self._all_faulted = any(fault is not None and (fault["stop_policy"] == "all" or fault["exception_stop_all"]) for fault in self._faults)

    def get_telemetry(self) -> list:
        """读取每路八字段及末尾全使能位的遥测快照。

        ==================
        Read eight fields per motor followed by the all-enabled flag.

        Args:
            无 / None.

        Returns:
            list：每路 target,RPM,PWM,error,Kp,Ki,Kd,enabled，末尾全使能位 / Telemetry snapshot.

        Raises:
            无主动抛出 / No explicit exceptions.

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

    def _reset_guard(self, index: int) -> None:
        if type(index) is not int or not 0 <= index < len(self._faults):
            raise ValueError("Invalid guard index")
        self._guard_start[index] = None
        self._guard_since[index] = None
        self._guard_sign[index] = 0

    def _assert_can_drive(self, motor_id: int) -> None:
        index = self._index(motor_id)
        if self._all_faulted or self._faults[index] is not None:
            raise RuntimeError("Feedback fault latched; clear_faults() before starting")

    def _check_feedback(self, index: int, count: int, now: int, pwm: float) -> bool:
        if type(index) is not int or not 0 <= index < len(self._faults):
            raise ValueError("Invalid guard index")
        config = self._feedback_protection
        pid = self._pids[index]
        sign = (pid.target > 0) - (pid.target < 0)
        if not config["enabled"] or not pid.enabled or not sign:
            self._reset_guard(index)
            self._guard_count[index] = count
            return False
        if self._guard_start[index] is None or sign != self._guard_sign[index]:
            self._guard_start[index] = now
            self._guard_since[index] = None
            self._guard_sign[index] = sign
        driven = abs(pwm) > config["pwm_threshold"]
        if count != self._guard_count[index]:
            self._guard_count[index] = count
            self._guard_since[index] = now if driven else None
        if not driven:
            self._guard_since[index] = None
            return False
        if self._guard_since[index] is None:
            self._guard_since[index] = now
        if (
            time.ticks_diff(now, self._guard_start[index]) < config["startup_grace_ms"]
            or time.ticks_diff(now, self._guard_since[index]) < config["timeout_ms"]
        ):
            return False
        # 先锁存故障，再尝试关断；关断失败也不能重新启动。
        self._faults[index] = dict(
            motor_id=index + 1,
            reason="no_feedback",
            latched=True,
            detected_ms=now,
            target_rpm=pid.target,
            pwm=pwm,
            count=count,
            stop_policy=config["stop_policy"],
            stop_attempted=False,
            stop_writes_ok=False,
            stop_attempts=0,
            stop_error=None,
            last_stop_attempt_ms=None,
            exception_stop_all=False,
        )
        if config["stop_policy"] == "all":
            self._all_faulted = True
        self._attempt_fault_stop()
        return True

    def _attempt_fault_stop(self, force_all: bool = False) -> None:
        if type(force_all) is not bool:
            raise ValueError("force_all must be bool")
        pending = [fault for fault in self._faults if fault is not None and (force_all or not fault["stop_writes_ok"])]
        if not pending and not force_all:
            return
        error = None
        if force_all and pending:
            self._all_faulted = True
        if self._all_faulted or force_all:
            try:
                self.stop_all()
            except Exception as exc:
                error = exc
        else:
            for fault in pending:
                try:
                    self.stop_motor(fault["motor_id"])
                except Exception as exc:
                    error = error or exc
        for fault in pending:
            if force_all:
                fault["exception_stop_all"] = True
            fault["stop_attempted"] = True
            fault["stop_writes_ok"] = error is None
            fault["stop_attempts"] += 1
            fault["last_stop_attempt_ms"] = time.ticks_ms()
            if error is not None and fault["stop_error"] is None:
                fault["stop_error"] = str(error)
        if error is not None:
            raise error

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
