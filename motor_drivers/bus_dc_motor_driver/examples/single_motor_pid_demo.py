# Python env   : MicroPython v1.29.0 / ESP32-C3
# -*- coding: utf-8 -*-
# @Time    : 2026/11/09
# @Author  : 赵岩松
# @File    : single_motor_pid_demo.py
# @Description : 正式BusDCMotor单路在线改速及连续正反转，不在在线阶段之间停机
# @License : MIT

"""正式库公开接口示例；七模块装入/lib，接线和使用方法见README。
Uses installed BusDCMotor, without replacing PID, motor writes or encoder methods.
"""

__version__ = "1.1.0"
__author__ = "赵岩松"
__license__ = "MIT"
__platform__ = "MicroPython v1.29.0 / ESP32-C3"

# ======================================== 导入相关模块 ========================================
import time
from machine import Pin, I2C
from pca9685 import PCA9685
from bus_dc_motor import BusDCMotor
from voltage_monitor import VoltageMonitor

# ======================================== 全局变量 ========================================
ARM_MOTORS = False
PERIOD_MS = 100
ENCODER_PINS = ((5, 6), (7, 8), (3, 2), (1, 0))
PID_PARAMS = ((0.15, 0.6, 0),) * 4
FEEDBACK_PROTECTION = {"startup_grace_ms": 4000, "timeout_ms": 2500, "pwm_threshold": 25, "stop_policy": "all"}
# 每段：(四路目标RPM, 秒数, 是否先停再启动)。False表示直接在线修改，不能先stop绕过换向。
STAGES = (
    ((30, 0, 0, 0), 6, False),
    ((-30, 0, 0, 0), 6, False),
    ((30, 0, 0, 0), 6, False),
    ((-30, 0, 0, 0), 6, False),
    ((30, 0, 0, 0), 6, False),
    ((60, 0, 0, 0), 6, False),
    ((-60, 0, 0, 0), 6, False),
    ((60, 0, 0, 0), 6, False),
    ((-60, 0, 0, 0), 6, False),
    ((60, 0, 0, 0), 6, False),
    ((0, 0, 0, 0), 2, False),
    ((-30, 0, 0, 0), 6, True),
)


# ======================================== 功能函数 ========================================
def create_pca() -> object:
    """本台架I2C0 SCL9/SDA10、400kHz、0x4F；失败释放自有总线。"""
    i2c = I2C(0, scl=Pin(9), sda=Pin(10), freq=400000)
    try:
        if 0x4F not in i2c.scan():
            raise RuntimeError("PCA9685 not found at 0x4F")
        pca = PCA9685(i2c, 0x4F)
        # 安装库管理频率；这里只初始化自动递增位并确保上电输出关闭。
        i2c.writeto_mem(0x4F, 0, b"\x20")
        for channel in range(8):
            pca.duty(channel, 0)
        return pca
    except BaseException:
        try:
            i2c.deinit()
        except Exception:
            pass
        raise


def recover_after_check(motor: object, confirmed: bool = False) -> None:
    """应用查明并排除原因后才传True；清除和启动是两个独立公开调用。"""
    if type(confirmed) is not bool or not confirmed:
        raise RuntimeError("Inspect fault and remove its cause before confirming recovery")
    print("RECOVERY_BEFORE", motor.get_faults())
    motor.clear_faults()
    print("RECOVERY_CLEARED", motor.get_faults(), motor.get_modes())
    motor.start_all()
    print("RECOVERY_STARTED", motor.get_modes())


def run_profile(stages: tuple, armed: bool = False) -> None:
    """有限时长普通调用；D供PC实时绘图，OBS保留计数/方向/模式/故障。"""
    if not armed:
        print("Motion disabled. Check wiring and set ARM_MOTORS=True.")
        return
    for targets, seconds, restart in stages:
        if len(targets) != 4 or not 0 < seconds <= 20 or type(restart) is not bool:
            raise ValueError("Expected four targets, duration in (0,20] and restart bool")
        if any(type(rpm) not in (int, float) or not -60 <= rpm <= 60 for rpm in targets):
            raise ValueError("Example targets must be finite numbers within -60..60 RPM")
    motor = pca = voltage = None
    failed = False
    time.sleep(3)
    try:
        pca = create_pca()
        voltage = VoltageMonitor(pin=4, interval_ms=200)
        voltage.update()
        if not 6 < voltage.get_voltage() < 9:
            raise RuntimeError("Check motor supply; example requires 6..9 V")
        motor = BusDCMotor(
            pca,
            4,
            encoder_pins=ENCODER_PINS,
            pid_params=PID_PARAMS,
            voltage_monitor=voltage,
            startup_brake=False,
            output_limit=(-50, 50),
            control_period_ms=PERIOD_MS,
            feedback_protection=FEEDBACK_PROTECTION,
        )
        for motor_id in range(1, 5):
            motor.set_pid(motor_id, 0.15, 0.6, 0)
        print("PUBLIC_EXAMPLE_BEGIN,single_motor_pid_demo")
        print("PROTECTION", motor.get_feedback_protection())
        previous_print = 0
        for stage, (targets, seconds, restart) in enumerate(stages, 1):
            if restart:
                motor.stop_all()
                print("EXPLICIT_STOP_BEFORE_START", stage, motor.get_modes())
            motor.set_target_rpm(1, targets[0])
            # 已使能路的重复start不会停止输出或重新开启宽限。
            for motor_id, target in enumerate(targets, 1):
                if target:
                    motor.start_motor(motor_id)
            print("STAGE", stage, targets, seconds, "stop/start" if restart else "online")
            print("CONFIG,%d,0.15,0.6,0,100" % stage)
            start = time.ticks_ms()
            last = start
            while time.ticks_diff(time.ticks_ms(), start) < seconds * 1000:
                tick = time.ticks_ms()
                begin = time.ticks_us()
                updated = motor.update()
                update_us = time.ticks_diff(time.ticks_us(), begin)
                if updated:
                    fields = motor.get_telemetry()
                    supply = motor.get_voltage()
                    faults = motor.get_faults()
                    modes = motor.get_modes()
                    if not 6 < supply < 9 or any(abs(motor.get_motor_rpm(i)) > 600 for i in range(1, 5)):
                        raise RuntimeError("Supply or encoder speed outside example range")
                    if faults:
                        print("FAULT", stage, time.ticks_diff(tick, start), faults)
                        raise RuntimeError("Latched feedback fault; inspect before explicit recovery")
                    now = time.ticks_ms()
                    elapsed = time.ticks_diff(now, start)
                    row = [stage, PERIOD_MS, elapsed]
                    row += [fields[i * 8] for i in range(4)]
                    row += [fields[i * 8 + 1] for i in range(4)]
                    row += [fields[i * 8 + 2] for i in range(4)]
                    row += [supply, update_us, -1, -1, previous_print, time.ticks_diff(now, last)]
                    last = now
                    begin = time.ticks_us()
                    print("D," + ",".join(str(value) for value in row))
                    for i in range(4):
                        print(
                            "OBS,%d,%d,%d,%s,%s,%s,%d,%d,%s,%s,%s"
                            % (
                                stage,
                                elapsed,
                                i + 1,
                                fields[i * 8],
                                fields[i * 8 + 1],
                                fields[i * 8 + 2],
                                motor.get_encoder_count(i + 1),
                                motor.get_encoder_direction(i + 1),
                                supply,
                                modes[i],
                                "none",
                            )
                        )
                    previous_print = time.ticks_diff(time.ticks_us(), begin)
                time.sleep_ms(5)
        motor.stop_all()
        print("PUBLIC_EXAMPLE_END,single_motor_pid_demo", motor.get_modes(), motor.get_faults())
    except BaseException:
        failed = True
        raise
    finally:
        error = None
        for resource in (motor, voltage, pca, pca.i2c if pca is not None else None):
            if resource is not None and hasattr(resource, "deinit"):
                try:
                    resource.deinit()
                except Exception as exc:
                    error = error or exc
        if error is not None and not failed:
            raise error
        print("PUBLIC_EXAMPLE_CLEANUP,single_motor_pid_demo")


def run(armed: bool = False, seconds: int = 6) -> None:
    """默认禁止运动；PC采集器可传每段5..20秒，零目标段固定两秒。"""
    if type(seconds) is not int or not 5 <= seconds <= 20:
        raise ValueError("seconds must be an integer within 5..20")
    stages = tuple((targets, seconds if any(targets) else 2, restart) for targets, _, restart in STAGES)
    run_profile(stages, armed)


# ======================================== 自定义类 ========================================
# ======================================== 初始化配置 ========================================
# ======================================== 主程序 ========================================
if __name__ == "__main__":
    run(ARM_MOTORS)
