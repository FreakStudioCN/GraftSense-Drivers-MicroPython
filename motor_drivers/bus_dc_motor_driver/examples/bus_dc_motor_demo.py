# Python env   : MicroPython v1.29.0 / ESP32-C3
# -*- coding: utf-8 -*-
# @Time    : 2026/11/06
# @Author  : 赵岩松
# @File    : bus_dc_motor_demo.py
# @Description : 电机驱动独立调用示例
# @License : MIT

__version__ = "1.1.0"
__author__ = "赵岩松"
__license__ = "MIT"
__platform__ = "MicroPython v1.29.0 / ESP32-C3"

# 单文件测试：除 code/ 中的驱动外，不依赖其他测试脚本。

# ======================================== 导入相关模块 ========================================
import time
from bus_dc_motor import BusDCMotor
from voltage_monitor import VoltageMonitor
from machine import Pin, I2C
from pca9685 import PCA9685


# ======================================== 全局变量 ========================================
ARM_MOTORS = False
ENCODER_PINS = ((5, 6), (7, 8), (3, 2), (1, 0))
PID_PARAMS = ((0.15, 0.6, 0),) * 4


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


def read_pairs(pca: object) -> list:
    """读取八通道原始寄存器，验证 full-on/off 与 PWM 原值。"""
    result = []
    for channel in range(8):
        data = pca.i2c.readfrom_mem(pca.address, 6 + 4 * channel, 4)
        result.append((data[0] | data[1] << 8, data[2] | data[3] << 8))
    return result


# ======================================== 自定义类 ========================================


# ======================================== 初始化配置 ========================================


# ======================================== 主程序 ========================================
def run() -> None:
    if not ARM_MOTORS:
        print("Motion disabled. Set ARM_MOTORS=True to run compatibility test.")
        return
    time.sleep(3)
    print("FreakStudio: BusDCMotor compatibility test")
    motor = None
    pca = None
    voltage = None
    failed = False
    try:
        pca = create_pca()
        # 原构造参数与默认全通道刹车保持兼容。
        motor = BusDCMotor(pca, 4)
        assert read_pairs(pca) == [(4096, 0)] * 8
        motor.stop_all()
        print("PASS: legacy constructor sets all eight channels full-on brake")
        voltage = VoltageMonitor(pin=4)
        motor = BusDCMotor(
            pca,
            4,
            encoder_pins=ENCODER_PINS,
            pid_params=PID_PARAMS,
            voltage_monitor=voltage,
            startup_brake=False,
            output_limit=(-50, 50),
        )
        time.sleep_ms(100)
        motor.update()
        if not 6 < motor.get_voltage() < 9:
            raise RuntimeError("Example requires motor supply within 6..9 V")
        print("stage,elapsed_ms,id,target_rpm,actual_rpm,pwm,count,direction,voltage,mode")

        def sample(stage: str, seconds: float) -> None:
            start = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), start) < seconds * 1000:
                if motor.update():
                    faults = motor.get_faults()
                    if faults:
                        raise RuntimeError("Latched motor fault: %s" % (faults,))
                    fields = motor.get_telemetry()
                    modes = motor.get_modes()
                    supply = motor.get_voltage()
                    if not 6 < supply < 9:
                        raise RuntimeError("Supply outside example range")
                    for i in range(4):
                        rpm = motor.get_motor_rpm(i + 1)
                        target = fields[i * 8]
                        if abs(rpm) > 600:
                            raise RuntimeError("Unexpected encoder speed")
                        if modes[i] == "pid" and (rpm * target < -10 * abs(target) or abs(rpm) > 150):
                            raise RuntimeError("Unexpected closed-loop direction or speed")
                        print(
                            "%s,%d,%d,%s,%s,%s,%d,%d,%s,%s"
                            % (
                                stage,
                                time.ticks_diff(time.ticks_ms(), start),
                                i + 1,
                                target,
                                rpm,
                                fields[i * 8 + 2],
                                motor.get_encoder_count(i + 1),
                                motor.get_encoder_direction(i + 1),
                                supply,
                                modes[i],
                            )
                        )
                time.sleep_ms(5)

        # 原 PWM 单位与 0/1 方向接口，不将 1900 误解释为 RPM。
        motor.set_motor_speed(1, 1900, 0)
        assert read_pairs(pca)[:2] == [(0, 1900), (0, 4096)]
        sample("legacy_forward", 2)
        motor.stop_motor(1)
        sample("legacy_stop", 2)
        motor.set_motor_speed(1, 1900, 1)
        assert read_pairs(pca)[:2] == [(0, 4096), (0, 1900)]
        sample("legacy_reverse", 2)
        motor.break_motor(1)
        sample("legacy_brake", 1)
        assert read_pairs(pca)[:2] == [(4096, 0)] * 2
        print("PASS: legacy PWM, direction, stop and brake survive update")
        motor.stop_all()
        sample("pause", 2)

        # 参数和目标在统一入口设置，但显式 start 才开始 PID。
        for target in (30, -30):
            motor.set_pid(1, 0.15, 0.6, 0)
            motor.set_target_rpm(1, target)
            assert read_pairs(pca)[:2] == [(0, 4096)] * 2
            motor.start_motor(1)
            sample("single_pid_" + str(target), 8)
            motor.stop_motor(1)
            sample("pause", 2)

        # M1 开环与 M2 PID 并行；验证彼此不会覆盖。
        motor.set_motor_speed(1, 1900, 0)
        motor.set_target_rpm(2, 30)
        motor.start_motor(2)
        sample("mixed_open_pid", 3)
        assert read_pairs(pca)[:2] == [(0, 1900), (0, 4096)]
        motor.stop_all()
        sample("pause", 2)
        print("PASS: open-loop and PID coexist")

        motor.set_target_rpms((30, -40, 50, -60))
        motor.start_all()
        sample("four_pid", 10)
        motor.stop_all()
        motor.set_target_rpms((0, 0, 0, 0))
        sample("final_stop", 2)
        assert read_pairs(pca) == [(0, 4096)] * 8
        assert motor.get_modes() == ("stopped",) * 4
        print("PASS: all outputs stopped; target RPMs cleared")
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
        print("Compatibility test failed:", exc)
        raise
    finally:
        error = None
        for resource in (motor, voltage, pca, pca.i2c if pca is not None else None):
            if resource is not None and hasattr(resource, "deinit"):
                try:
                    resource.deinit()
                except Exception as exc:
                    if error is None:
                        error = exc
        if error is not None and not failed:
            raise error
        print("All configured motors stopped; owned resources released")


if __name__ == "__main__":
    run()
