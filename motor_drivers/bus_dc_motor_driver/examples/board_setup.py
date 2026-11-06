# Python env   : MicroPython v1.29.0 / ESP32-C3
# -*- coding: utf-8 -*-
# @Time    : 2026/11/06
# @Author  : 赵岩松
# @File    : board_setup.py
# @Description : 示例共用硬件配置；上传到 /lib/board_setup.py，不作为启动入口。
# @License : MIT

# ======================================== 导入相关模块 ========================================
import time
from machine import Pin, I2C
from pca9685 import PCA9685
from motor_controller import MotorController
from voltage_monitor import VoltageMonitor

# ======================================== 全局变量 ========================================
MOTOR_CONFIGS = ((0, 1, 5, 6), (2, 3, 7, 8), (4, 5, 3, 2), (6, 7, 1, 0))
PID_PARAMS = ((0.15, 0.6, 0.0),) * 4
PPR = 13
GEAR_RATIO = 20
PERIOD_MS = 100


# ======================================== 功能函数 ========================================
def create_pca() -> object:
    """扫描设备，将全部电机通道关闭，再设置整片 PWM 为 1000 Hz。"""
    i2c = I2C(0, scl=Pin(9), sda=Pin(10), freq=400000)
    try:
        devices = i2c.scan()
        print("I2C devices:", [hex(x) for x in devices])
        if not devices:
            raise RuntimeError("No I2C device found")
        if 0x4F not in devices:
            raise RuntimeError("Device not found at expected address")
        # 无固定芯片 ID；构造及频率设置通过寄存器读写验证响应。
        pca = PCA9685(i2c, 0x4F)
        # reset() 清除了自动递增位；pwm() 的四字节寄存器写入需要先启用它。
        pca.i2c.writeto_mem(pca.address, 0x00, b"\x20")
        for channel in range(8):
            pca.duty(channel, 0)
        pca.freq(1000)
        return pca
    except BaseException:
        try:
            if hasattr(i2c, "deinit"):
                i2c.deinit()
        except Exception:
            pass
        raise


def create_controller(pca: object = None) -> object:
    """只创建并停止四路，示例限幅为 ±50%，不改变正式入口配置。"""
    owned = pca is None
    if owned:
        pca = create_pca()
    try:
        return MotorController(
            pca,
            MOTOR_CONFIGS,
            PID_PARAMS,
            ppr=PPR,
            gear_ratio=GEAR_RATIO,
            output_limit=(-50, 50),
            integral_limit=(-50, 50),
        )
    except BaseException:
        if owned:
            try:
                if hasattr(pca.i2c, "deinit"):
                    pca.i2c.deinit()
            except Exception:
                pass
        raise


def stop_all(controller: object) -> None:
    """停止输出并清零目标；即使清零异常也尝试停止输出。"""
    try:
        controller.set_target_rpms((0, 0, 0, 0))
    finally:
        controller.stop_all()


# ======================================== 自定义类 ========================================
# ======================================== 初始化配置 ========================================
# ======================================== 主程序 ========================================
def run_profile(stages: tuple, armed: bool = False) -> None:
    """每段 (四路目标RPM, 秒数)，打印目标/反馈/PWM/计数/电压，组间停三秒。"""
    if not armed:
        print("Motion disabled. Review stages and set ARM_MOTORS=True.")
        return
    # 先验证整个序列，避免中途发现配置错误。
    for targets, seconds in stages:
        if len(targets) != 4 or not 0 < seconds <= 30:
            raise ValueError("Expected four targets and duration in (0,30]")
        if any(not -60 <= rpm <= 60 for rpm in targets):
            raise ValueError("Example targets must be within -60..60 RPM")
    time.sleep(3)
    print("FreakStudio: independent PID profile")
    controller = None
    pca = None
    voltage = None
    failed = False
    try:
        pca = create_pca()
        controller = create_controller(pca)
        voltage = VoltageMonitor(pin=4, interval_ms=200)
        voltage.update()
        if not 6 < voltage.get_voltage() < 9:
            raise RuntimeError("Check motor supply; example requires 6..9 V")
        print("stage,elapsed_ms,id,target_rpm,actual_rpm,pwm,count,direction,voltage")
        for stage, (targets, seconds) in enumerate(stages):
            stop_all(controller)
            # 运行中修改参数的统一接口；这里只重复设置当前候选值。
            for motor_id in range(1, 5):
                controller.set_pid(motor_id, 0.15, 0.6, 0)
            controller.set_target_rpms(targets)
            for motor_id, rpm in enumerate(targets, 1):
                if rpm:
                    controller.start_motor(motor_id)
            start = time.ticks_ms()
            last = start
            while time.ticks_diff(time.ticks_ms(), start) < seconds * 1000:
                now = time.ticks_ms()
                if time.ticks_diff(now, last) >= PERIOD_MS:
                    last = now
                    controller.update()
                    voltage.update()
                    supply = voltage.get_voltage()
                    if not 6 < supply < 9:
                        raise RuntimeError("Supply outside example range")
                    telemetry = controller.get_telemetry()
                    for i, target in enumerate(targets):
                        rpm = controller.get_motor_rpm(i + 1)
                        pwm = telemetry[i * 8 + 2]
                        if abs(rpm) > 150 or rpm * target < -10 * abs(target):
                            raise RuntimeError("Unexpected encoder speed or direction")
                        if time.ticks_diff(now, start) > 3000 and target and abs(rpm) < 1 and abs(pwm) > 25:
                            raise RuntimeError("No encoder feedback under drive")
                        print(
                            "%d,%d,%d,%s,%s,%s,%d,%d,%s"
                            % (
                                stage + 1,
                                time.ticks_diff(now, start),
                                i + 1,
                                target,
                                rpm,
                                pwm,
                                controller.get_encoder_count(i + 1),
                                controller.get_encoder_direction(i + 1),
                                supply,
                            )
                        )
                time.sleep_ms(5)
            stop_all(controller)
            time.sleep(3)
    except KeyboardInterrupt:
        failed = True
        print("Interrupted")
        raise
    except OSError as exc:
        failed = True
        print("Hardware communication error:", exc)
        raise
    except Exception as exc:
        failed = True
        print("Profile failed:", exc)
        raise
    finally:
        error = None
        resources = (controller, voltage, pca, pca.i2c if pca is not None else None)
        for resource in resources:
            if resource is not None and hasattr(resource, "deinit"):
                try:
                    resource.deinit()
                except Exception as exc:
                    if error is None:
                        error = exc
        if error is not None and not failed:
            raise error
        print("All motors stopped; owned resources released")
