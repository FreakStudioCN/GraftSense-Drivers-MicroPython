# Python env   : MicroPython v1.29.0 / ESP32-C3
# -*- coding: utf-8 -*-
# @Time    : 2026/11/06
# @Author  : 赵岩松
# @File    : main.py
# @Description : 四路电机兼容开环与编码器闭环测试入口
# @License : MIT

# ======================================== 导入相关模块 ========================================
import time
from machine import Pin, I2C
from pca9685 import PCA9685
from bus_dc_motor import BusDCMotor

# ======================================== 全局变量 ========================================
ARM_MOTORS = False
MODE = "pid"
SCL_PIN = 9
SDA_PIN = 10
PCA_ADDRESS = 0x4F
PWM_FREQUENCY = 1000
ENCODER_PINS = ((5, 6), (7, 8), (3, 2), (1, 0))
PID_PARAMS = ((0.15, 0.6, 0),) * 4
TARGET_RPMS = (30, -40, 50, -60)
VOLTAGE_PIN = 4
RUN_SECONDS = 10
FEEDBACK_PROTECTION = {"startup_grace_ms": 4000, "timeout_ms": 2500, "pwm_threshold": 25, "stop_policy": "all"}
# ======================================== 功能函数 ========================================
# ======================================== 自定义类 ========================================
# ======================================== 初始化配置 ========================================


def _prepare_hardware() -> tuple:
    """显式启用后延时、扫描并创建本示例硬件 / Prepare hardware only when armed."""
    time.sleep(3)
    print("FreakStudio: four-motor driver test")
    i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)
    try:
        devices = i2c.scan()
        print("I2C devices:", [hex(a) for a in devices])
        if not devices:
            raise RuntimeError("No I2C device found")
        if PCA_ADDRESS not in devices:
            raise RuntimeError("Device not found at expected address")
        # 该器件无固定芯片 ID；构造时写 MODE1 检查通信响应。
        pca = PCA9685(i2c, PCA_ADDRESS)
        return i2c, pca
    except BaseException:
        try:
            if hasattr(i2c, "deinit"):
                i2c.deinit()
        except Exception:
            pass
        raise


# ======================================== 主程序 ========================================
def run() -> None:
    """执行有限时长测试；默认禁用，不创建硬件 / Run a bounded test only when armed."""
    if not ARM_MOTORS:
        print("FreakStudio: motors disabled; review wiring and set ARM_MOTORS=True")
        return
    if MODE not in ("legacy", "pid") or not 0 < RUN_SECONDS <= 30:
        raise ValueError("Check MODE and duration (0,30] seconds")
    i2c, pca = _prepare_hardware()
    motor = None
    voltage_monitor = None
    try:
        if MODE == "legacy":
            # 旧位置参数仍可用；新示例选择默认低电平停止，避免默认全高刹车。
            motor = BusDCMotor(pca, 4, startup_brake=False, pwm_frequency=PWM_FREQUENCY)
            motor.set_motor_speed(1, 1900, 0)
            time.sleep(2)
            motor.stop_motor(1)
            time.sleep(2)
            motor.set_motor_speed(1, 1900, 1)
            time.sleep(2)
            motor.break_motor(1)
            time.sleep(1)
        else:
            # 仅闭环/电压模式导入相关依赖，旧开环用法不占编码器与 ADC GPIO。
            from voltage_monitor import VoltageMonitor

            voltage_monitor = VoltageMonitor(pin=VOLTAGE_PIN)
            motor = BusDCMotor(
                pca,
                4,
                encoder_pins=ENCODER_PINS,
                pid_params=PID_PARAMS,
                voltage_monitor=voltage_monitor,
                ppr=13,
                gear_ratio=20,
                startup_brake=False,
                pwm_frequency=PWM_FREQUENCY,
                output_limit=(-50, 50),
                feedback_protection=FEEDBACK_PROTECTION,
            )
            time.sleep_ms(100)
            motor.update()
            print("Supply voltage:", motor.get_voltage())
            if not 6 < motor.get_voltage() < 9:
                raise RuntimeError("Check supply; this example expects 7.4 V motor system")
            motor.set_target_rpms(TARGET_RPMS)
            for i in range(1, 5):
                motor.set_pid(i, 0.15, 0.6, 0)
            motor.start_all()
            start = time.ticks_ms()
            print("elapsed_ms,id,target_rpm,actual_rpm,pwm,count,direction,voltage")
            while time.ticks_diff(time.ticks_ms(), start) < RUN_SECONDS * 1000:
                if motor.update():
                    faults = motor.get_faults()
                    if faults:
                        print("Latched motor fault:", faults)
                        break
                    voltage = motor.get_voltage()
                    if not 6 < voltage < 9:
                        raise RuntimeError("Supply outside example range")
                    fields = motor.get_telemetry()
                    for i in range(1, 5):
                        print(
                            "%d,%d,%s,%s,%s,%d,%d,%s"
                            % (
                                time.ticks_diff(time.ticks_ms(), start),
                                i,
                                TARGET_RPMS[i - 1],
                                motor.get_motor_rpm(i),
                                fields[(i - 1) * 8 + 2],
                                motor.get_encoder_count(i),
                                motor.get_encoder_direction(i),
                                voltage,
                            )
                        )
                time.sleep_ms(5)
    except KeyboardInterrupt:
        print("Interrupted")
        raise
    except OSError as exc:
        print("Hardware communication error:", exc)
        raise
    except Exception as exc:
        print("Motor example failed:", exc)
        raise
    finally:
        try:
            if motor is not None:
                try:
                    motor.stop_all()
                    if MODE == "pid":
                        motor.set_target_rpms((0, 0, 0, 0))
                finally:
                    motor.deinit()
        finally:
            # 本示例拥有 ADC；驱动兼容入口不释放调用方注入的监测器。
            try:
                if voltage_monitor is not None:
                    voltage_monitor.deinit()
            finally:
                pca.deinit()
                if hasattr(i2c, "deinit"):
                    i2c.deinit()
        print("All configured motors stopped; resources released")


if __name__ == "__main__":
    run()
