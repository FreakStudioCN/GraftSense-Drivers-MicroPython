# Python env   : MicroPython v1.29.0 / ESP32-C3
# -*- coding: utf-8 -*-
# @Time    : 2026/11/06
# @Author  : 李清水
# @File    : bus_dc_motor.py
# @Description : 兼容原接口的四路电机 PWM、编码器与 PID 入口
# @License : MIT

__version__ = "1.1.0"
__author__ = "李清水"
__license__ = "MIT"
__platform__ = "MicroPython v1.29.0 / ESP32-C3"

# 原库来源：leezisheng/GraftSense-Drivers-MicroPython
# 原库基线：59d748fb2529b73c302d73bb5fcd1f358b4151ff

# ======================================== 导入相关模块 ========================================
import math
import time
from pca9685 import PCA9685


# ======================================== 全局变量 ========================================
# ======================================== 功能函数 ========================================
def _finite(value: float, name: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(name + " must be finite")
    return value


# ======================================== 自定义类 ========================================
class BusDCMotor:
    """原库兼容入口及可选闭环控制。

    ==================
    Backward-compatible PWM facade with optional encoder PID.

    Attributes:
        pca9685、motor_count 为共享驱动与电机数 / Borrowed PWM driver and motor count.
    Methods:
        set_motor_speed、set_target_rpm、set_pid、update、stop_all、deinit。
    Notes:
        只有 update 执行周期闭环；设置目标不自动启动。每路仅一种输出模式。 / Call update regularly; setting a target never starts output.
    """

    def __init__(
        self,
        pca9685: PCA9685,
        motor_count: int = 4,
        *,
        encoder_pins: object = None,
        pid_params: object = None,
        voltage_monitor: object = None,
        ppr: int = 13,
        gear_ratio: float = 20,
        control_period_ms: int = 100,
        output_limit: tuple = (-100, 100),
        integral_limit: tuple = (-50, 50),
        startup_brake: bool = True,
        pwm_frequency: float = 1000
    ) -> None:
        """校验配置并创建实例。

        ==================
        Validate configuration and initialize the instance.

        Args:
            pca9685: 调用方提供的 PCA9685 实例 / Caller-owned PCA9685.
            motor_count: 电机数量 1..4 / Number of motors, 1..4.
            encoder_pins: 按 ID 排列的 GPIO A/B 对；None 禁用反馈 / Pin pairs, or None.
            pid_params: 按 ID 排列的 (Kp, Ki, Kd) / Gain triples in motor-ID order.
            voltage_monitor: 电压监测实例或 None；本类不拥有 ADC / Borrowed monitor or None.
            ppr: A 相上升沿计数时电机轴每圈脉冲数 / A-rising counts per motor revolution.
            gear_ratio: 电机轴到输出轴减速比 / Motor-to-output reduction ratio.
            control_period_ms: 两次闭环更新最小间隔 ms / Minimum loop interval in ms.
            output_limit: 输出下限、上限，PWM 百分比 / Output bounds in PWM percent.
            integral_limit: 积分状态下限、上限；尚未乘 Ki / Integral-state bounds before Ki.
            startup_brake: True 保留原库八通道全高刹车 / Legacy eight-channel brake if True.
            pwm_frequency: 整片共用 PWM 频率，24..1526 Hz / Shared chip PWM frequency in Hz.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception. RuntimeError：所需反馈/电压模块未配置 / Required feedback or voltage monitor is absent.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if not isinstance(startup_brake, bool):
            raise ValueError("startup_brake must be bool")
        if voltage_monitor is not None and (
            not hasattr(voltage_monitor, "update")
            or not hasattr(voltage_monitor, "get_voltage")
        ):
            raise ValueError("voltage_monitor must provide update() and get_voltage()")
        if type(motor_count) is not int or not 1 <= motor_count <= 4:
            raise ValueError("Motor count must be 1..4")
        if not isinstance(pca9685, PCA9685):
            raise ValueError("pca9685 must be a PCA9685 instance")
        if type(control_period_ms) is not int or control_period_ms < 1:
            raise ValueError("Control period must be a positive integer")
        if not 24 <= _finite(pwm_frequency, "PWM frequency") <= 1526:
            raise ValueError("PWM frequency must be in range 24..1526 Hz")
        if encoder_pins is not None and (
            len(encoder_pins) != motor_count
            or any(len(pins) != 2 for pins in encoder_pins)
        ):
            raise ValueError("One A/B pin pair per motor is required")
        if pid_params is not None and (
            encoder_pins is None or len(pid_params) != motor_count
        ):
            raise ValueError("PID parameters require matching encoder configuration")
        self.pca9685 = pca9685
        self.motor_count = motor_count
        self._controller = None
        self._voltage = voltage_monitor
        self._modes = ["stopped"] * motor_count
        self._pwms = [0.0] * motor_count
        self._period = control_period_ms
        self._last_update = time.ticks_ms()
        try:
            # 保留原库整片频率设置，构造器不能与舵机频率独立共用。
            self.pca9685.freq(pwm_frequency)
            if encoder_pins is not None:
                from motor_controller import MotorController

                configs = [
                    (2 * i, 2 * i + 1, pins[0], pins[1])
                    for i, pins in enumerate(encoder_pins)
                ]
                params = (
                    pid_params
                    if pid_params is not None
                    else ((0.15, 0.6, 0),) * motor_count
                )
                self._controller = MotorController(
                    pca9685,
                    configs,
                    params,
                    ppr=ppr,
                    gear_ratio=gear_ratio,
                    output_limit=output_limit,
                    integral_limit=integral_limit,
                )
            if startup_brake:
                # 原构造器即使 motor_count 小于四，也会将全部八通道置高。
                for channel in range(8):
                    self.pca9685.duty(channel, 4095)
                self._modes = ["brake"] * motor_count
            else:
                self.stop_all()
        except BaseException:
            try:
                self.stop_all()
            except Exception:
                pass
            raise

    def set_motor_speed(self, motor_id: int, speed: int, direction: int = 0) -> None:
        """按旧接口设置 PWM 原值与方向，并关闭该路 PID。

        ==================
        Apply legacy raw PWM and direction; disable that motor PID.

        Args:
            motor_id: 从 1 开始的电机 ID / One-based motor ID.
            speed: 旧接口 PWM 原值 1900..4095，非 RPM / Legacy raw PWM value, not RPM.
            direction: 0 正转、1 反转 / 0 forward, 1 reverse.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception. RuntimeError：所需反馈/电压模块未配置 / Required feedback or voltage monitor is absent.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if type(motor_id) is not int or not 1 <= motor_id <= self.motor_count:
            raise ValueError("Invalid motor ID")
        i = self._index(motor_id)
        _finite(speed, "speed")
        if not 1900 <= speed <= 4095:
            raise ValueError("Speed must be in range 1900..4095")
        if type(direction) is not int or direction not in (0, 1):
            raise ValueError("Direction must be 0 or 1")
        try:
            self._disable_pid(motor_id)
            # 换向先关闭不使用的输入，避免旧 PWM 与新方向短时重叠。
            active = 2 * i + direction
            inactive = 2 * i + 1 - direction
            self.pca9685.duty(inactive, 0)
            self.pca9685.duty(active, speed)
            self._modes[i] = "open"
            self._pwms[i] = speed * 100 / 4095 * (1 if direction == 0 else -1)
        except BaseException:
            self.stop_all()
            raise

    def stop_motor(self, motor_id: int) -> None:
        """禁用指定 PID 并立即停止该路输出，保留目标。

        ==================
        Disable one PID and stop its output; retain the target.

        Args:
            motor_id: 从 1 开始的电机 ID / One-based motor ID.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception. RuntimeError：所需反馈/电压模块未配置 / Required feedback or voltage monitor is absent.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if type(motor_id) is not int or not 1 <= motor_id <= self.motor_count:
            raise ValueError("Invalid motor ID")
        i = self._index(motor_id)
        self._modes[i] = "stopped"
        self._pwms[i] = 0
        # 失败时也尝试两路输入关闭。
        error = None
        try:
            self._disable_pid(motor_id)
        except Exception as exc:
            error = exc
        for channel in (2 * i, 2 * i + 1):
            try:
                self.pca9685.duty(channel, 0)
            except Exception as exc:
                error = error or exc
        if error is not None:
            raise error

    def break_motor(self, motor_id: int) -> None:
        """禁用 PID 后双输入置高刹车，保留原接口拼写。

        ==================
        Disable PID and brake with both inputs high; retain legacy spelling.

        Args:
            motor_id: 从 1 开始的电机 ID / One-based motor ID.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception. RuntimeError：所需反馈/电压模块未配置 / Required feedback or voltage monitor is absent.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if type(motor_id) is not int or not 1 <= motor_id <= self.motor_count:
            raise ValueError("Invalid motor ID")
        i = self._index(motor_id)
        try:
            self.stop_motor(motor_id)
            self.pca9685.duty(2 * i, 4095)
            self.pca9685.duty(2 * i + 1, 4095)
            self._modes[i] = "brake"
        except BaseException:
            self.stop_all()
            raise

    def stop_all(self) -> None:
        """尝试停止全部电机；某路失败仍处理其他路，最后抛首个异常。

        ==================
        Attempt every motor stop and then raise the first failure.

        Args:
            无 / None.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception. RuntimeError：所需反馈/电压模块未配置 / Required feedback or voltage monitor is absent.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        error = None
        for motor_id in range(1, self.motor_count + 1):
            try:
                self.stop_motor(motor_id)
            except Exception as exc:
                error = error or exc
        if error is not None:
            raise error

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
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception. RuntimeError：所需反馈/电压模块未配置 / Required feedback or voltage monitor is absent.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if type(motor_id) is not int or not 1 <= motor_id <= self.motor_count:
            raise ValueError("Invalid motor ID")
        i = self._index(motor_id)
        _finite(rpm, "rpm")
        controller = self._feedback()
        if self._modes[i] in ("open", "brake"):
            self.stop_motor(motor_id)
        controller.set_target_rpm(motor_id, rpm)

    def set_target_rpms(self, rpms: object) -> None:
        """按 ID 顺序设置全部目标；不自动启动。

        ==================
        Set all targets in ID order without starting motors.

        Args:
            rpms: 按电机 ID 排列的目标 RPM 序列 / Target RPM sequence in ID order.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception. RuntimeError：所需反馈/电压模块未配置 / Required feedback or voltage monitor is absent.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if len(rpms) != self.motor_count:
            raise ValueError("One RPM target per motor is required")
        for rpm in rpms:
            _finite(rpm, "rpm")
        self._feedback()
        for i, rpm in enumerate(rpms, 1):
            self.set_target_rpm(i, rpm)

    def set_pid(
        self, motor_id: int, kp: float = None, ki: float = None, kd: float = None
    ) -> None:
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
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception. RuntimeError：所需反馈/电压模块未配置 / Required feedback or voltage monitor is absent.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if type(motor_id) is not int or not 1 <= motor_id <= self.motor_count:
            raise ValueError("Invalid motor ID")
        self._index(motor_id)
        for value in (kp, ki, kd):
            if value is not None and _finite(value, "PID gain") < 0:
                raise ValueError("PID gains must be nonnegative")
        self._feedback().set_pid(motor_id, kp, ki, kd)

    def start_motor(self, motor_id: int) -> None:
        """使能指定闭环，下次 update 更新输出。

        ==================
        Enable one loop for output on the next update.

        Args:
            motor_id: 从 1 开始的电机 ID / One-based motor ID.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception. RuntimeError：所需反馈/电压模块未配置 / Required feedback or voltage monitor is absent.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if type(motor_id) is not int or not 1 <= motor_id <= self.motor_count:
            raise ValueError("Invalid motor ID")
        i = self._index(motor_id)
        controller = self._feedback()
        if self._modes[i] != "pid":
            self.stop_motor(motor_id)
        controller.start_motor(motor_id)
        self._modes[i] = "pid"

    def start_all(self) -> None:
        """使能全部闭环，保留各自目标。

        ==================
        Enable all loops while retaining their targets.

        Args:
            无 / None.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception. RuntimeError：所需反馈/电压模块未配置 / Required feedback or voltage monitor is absent.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        self._feedback()
        try:
            for motor_id in range(1, self.motor_count + 1):
                self.start_motor(motor_id)
        except BaseException:
            self.stop_all()
            raise

    def get_motor_rpm(self, motor_id: int) -> float:
        """读取最近一次更新得到的带符号 RPM。

        ==================
        Read signed RPM from the latest update.

        Args:
            motor_id: 从 1 开始的电机 ID / One-based motor ID.

        Returns:
            float：RPM 或 PID 输出，单位见上述说明 / RPM or PID output as described.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception. RuntimeError：所需反馈/电压模块未配置 / Required feedback or voltage monitor is absent.

        Notes:
            仅读取状态；不写硬件 / Read state only; no hardware writes.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if type(motor_id) is not int or not 1 <= motor_id <= self.motor_count:
            raise ValueError("Invalid motor ID")
        self._index(motor_id)
        return self._feedback().get_motor_rpm(motor_id)

    def get_encoder_count(self, motor_id: int) -> int:
        """读取实时累计有符号脉冲计数。

        ==================
        Read the current signed accumulated pulse count.

        Args:
            motor_id: 从 1 开始的电机 ID / One-based motor ID.

        Returns:
            int：计数、方向或应用值，含义见上述说明 / Count, direction or applied value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception. RuntimeError：所需反馈/电压模块未配置 / Required feedback or voltage monitor is absent.

        Notes:
            仅读取状态；不写硬件 / Read state only; no hardware writes.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if type(motor_id) is not int or not 1 <= motor_id <= self.motor_count:
            raise ValueError("Invalid motor ID")
        self._index(motor_id)
        return self._feedback().get_encoder_count(motor_id)

    def get_encoder_direction(self, motor_id: int) -> int:
        """读取最后一个脉冲的方向，停止后可能保持旧值。

        ==================
        Read the last pulse direction, which may persist after stopping.

        Args:
            motor_id: 从 1 开始的电机 ID / One-based motor ID.

        Returns:
            int：计数、方向或应用值，含义见上述说明 / Count, direction or applied value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception. RuntimeError：所需反馈/电压模块未配置 / Required feedback or voltage monitor is absent.

        Notes:
            仅读取状态；不写硬件 / Read state only; no hardware writes.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if type(motor_id) is not int or not 1 <= motor_id <= self.motor_count:
            raise ValueError("Invalid motor ID")
        self._index(motor_id)
        return self._feedback().get_encoder_direction(motor_id)

    def get_voltage(self) -> object:
        """读取缓存的电机供电电压，首次采样前为 None。

        ==================
        Read cached supply volts, or None before the first sample.

        Args:
            无 / None.

        Returns:
            float 或 None：缓存电压 V / Cached volts, or None before sampling.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception. RuntimeError：所需反馈/电压模块未配置 / Required feedback or voltage monitor is absent.

        Notes:
            仅读取状态；不写硬件 / Read state only; no hardware writes.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if self._voltage is None:
            raise RuntimeError("Supply voltage monitor not configured")
        return self._voltage.get_voltage()

    def get_telemetry(self) -> list:
        """读取每路八字段及末尾全使能位的遥测快照。

        ==================
        Read eight fields per motor followed by the all-enabled flag.

        Args:
            无 / None.

        Returns:
            list：每路 target,RPM,PWM,error,Kp,Ki,Kd,enabled，末尾全使能位 / Telemetry snapshot.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception. RuntimeError：所需反馈/电压模块未配置 / Required feedback or voltage monitor is absent.

        Notes:
            仅读取状态；不写硬件 / Read state only; no hardware writes.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        data = self._feedback().get_telemetry()
        for i, mode in enumerate(self._modes):
            if mode != "pid":
                data[8 * i + 2] = self._pwms[i]
        return data

    def get_modes(self) -> tuple:
        """读取每路 stopped/open/pid/brake 模式。

        ==================
        Read each motor mode: stopped, open, pid or brake.

        Args:
            无 / None.

        Returns:
            tuple：按电机 ID 排列的模式字符串 / Modes in motor-ID order.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception. RuntimeError：所需反馈/电压模块未配置 / Required feedback or voltage monitor is absent.

        Notes:
            仅读取状态；不写硬件 / Read state only; no hardware writes.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        return tuple(self._modes)

    def update(self) -> bool:
        """到达周期后采集反馈，仅更新 PID 模式输出及电压缓存。

        ==================
        Update feedback, PID-mode outputs and voltage when the period elapses.

        Args:
            无 / None.

        Returns:
            bool：本次完成更新为 True，未到周期或 dt<=0 为 False / True if updated.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception. RuntimeError：所需反馈/电压模块未配置 / Required feedback or voltage monitor is absent.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_update) < self._period:
            return False
        try:
            if self._controller is not None:
                ids = [i + 1 for i, mode in enumerate(self._modes) if mode == "pid"]
                self._controller.update(motor_ids=ids)
                fields = self._controller.get_telemetry()
                for motor_id in ids:
                    self._pwms[motor_id - 1] = fields[(motor_id - 1) * 8 + 2]
            if self._voltage is not None:
                self._voltage.update()
            self._last_update = now
            return True
        except BaseException:
            try:
                self.stop_all()
            except Exception:
                pass
            raise

    def _index(self, motor_id: int) -> int:
        if type(motor_id) is not int or not 1 <= motor_id <= self.motor_count:
            raise ValueError("Invalid motor ID")
        return motor_id - 1

    def _feedback(self) -> object:
        if self._controller is None:
            raise RuntimeError("Configure encoder_pins for RPM/PID interfaces")
        return self._controller

    def _disable_pid(self, motor_id: int) -> None:
        if type(motor_id) is not int or not 1 <= motor_id <= self.motor_count:
            raise ValueError("Invalid motor ID")
        if self._controller is not None:
            self._controller.stop_motor(motor_id)

    def deinit(self) -> None:
        """停止电机并注销自有编码器 IRQ；保留共享 PCA 和电压监测器。

        ==================
        Stop motors and detach owned encoder IRQs; leave borrowed devices intact.

        Args:
            无 / None.
        Returns:
            None.
        Raises:
            Exception: 清理后传播首个底层异常 / First cleanup failure.
        Notes:
            即使停止失败也尝试注销 IRQ；调用方仍须处置输出故障。
            Attempts IRQ cleanup after a stop failure; caller handles failed outputs.
            不关闭调用方总线或 ADC；不可在 ISR 中调用 / Not ISR-safe.
        """
        error = None
        try:
            self.stop_all()
        except Exception as exc:
            error = exc
        if self._controller is not None:
            try:
                self._controller.deinit()
            except Exception as exc:
                error = error or exc
        if error is not None:
            raise error


# ======================================== 初始化配置 ========================================
# ======================================== 主程序 ========================================
