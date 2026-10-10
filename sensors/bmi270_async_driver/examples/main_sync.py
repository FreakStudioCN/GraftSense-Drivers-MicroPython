# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : 测试 BMI270 六轴IMU驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import I2C, Pin
from bmi270 import BMI270

# ======================================== 全局变量 ============================================
# BMI270 默认 I2C 地址
BMI270_I2C_ADDR = 0x68
# BMI270 WHO_AM_I 期望值
BMI270_CHIP_ID = 0x24
# BMI270 WHO_AM_I 寄存器地址
BMI270_WHO_AM_I_REG = 0x00
# 打印间隔（ms）
PRINT_INTERVAL = 2000
# 上次打印时间戳
last_print_time = 0
bmi270 = None


# ======================================== 功能函数 ============================================
def print_error_codes():
    """
    打印错误代码（调试功能，默认注释调用，可 REPL 手动调用）
    Print error codes (debug function, commented by default, can be called from REPL).
    """
    bmi270.error_code()


def switch_gyro_range():
    """
    切换陀螺仪量程到 ±1000 dps（模式切换，默认注释调用，可 REPL 手动触发）
    Switch gyro range to +/-1000 dps (mode switch, commented by default, can be triggered from REPL).
    """
    bmi270.gyro_range = bmi270.GYRO_RANGE_1000
    print("Gyro range switched to GYRO_RANGE_1000")


def switch_accel_range():
    """
    切换加速度量程到 ±8g（模式切换，默认注释调用，可 REPL 手动触发）
    Switch acceleration range to +/-8g (mode switch, commented by default, can be triggered from REPL).
    """
    bmi270.acceleration_range = bmi270.ACCEL_RANGE_8G
    print("Accel range switched to ACCEL_RANGE_8G")


# ======================================== 自定义类 ============================================
# 无自定义类，直接使用 bmi270.BMI270

# ======================================== 初始化配置 ==========================================
# 等待硬件就绪
time.sleep(3)
print("FreakStudio: Testing BMI270 6-axis IMU driver")

# 初始化 I2C 总线
# ESP32 示例引脚: scl=Pin(22), sda=Pin(21)
# Raspberry Pi Pico 示例引脚: scl=Pin(5), sda=Pin(4)
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# I2C 设备扫描
print("Scanning I2C bus...")
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("I2C devices found: %s" % [hex(d) for d in devices])

# 验证目标设备是否存在
if BMI270_I2C_ADDR not in devices:
    raise RuntimeError("BMI270 not found at expected address 0x%02X" % BMI270_I2C_ADDR)
print("BMI270 found at 0x%02X" % BMI270_I2C_ADDR)

# 读取并验证 WHO_AM_I 芯片 ID
chip_id = i2c.readfrom_mem(BMI270_I2C_ADDR, BMI270_WHO_AM_I_REG, 1)[0]
if chip_id != BMI270_CHIP_ID:
    raise RuntimeError("Unexpected BMI270 chip ID: expected 0x%02X, got 0x%02X" % (BMI270_CHIP_ID, chip_id))
print("BMI270 chip ID verified: 0x%02X" % chip_id)

# 创建 BMI270 传感器实例
bmi270 = BMI270(i2c, address=BMI270_I2C_ADDR, debug=False)
print("BMI270 initialized successfully")

# ========================================  主程序  ===========================================
last_print_time = time.ticks_ms()

try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
            # 读取加速度值（低频核心 API，保留自动执行）
            acc_x, acc_y, acc_z = bmi270.acceleration
            print("Accel (m/s^2): x=%.3f, y=%.3f, z=%.3f" % (acc_x, acc_y, acc_z))

            # 读取陀螺仪值（低频核心 API，保留自动执行）
            gyro_x, gyro_y, gyro_z = bmi270.gyro
            print("Gyro (dps): x=%.3f, y=%.3f, z=%.3f" % (gyro_x, gyro_y, gyro_z))

            # 打印当前量程设置（低频状态查询，保留自动执行）
            print("Range: accel=%s, gyro=%s" % (bmi270.acceleration_range, bmi270.gyro_range))
            print("Accel mode: %s" % bmi270.acceleration_operation_mode)
            print("---")
            last_print_time = current_time

        # 调试功能，注释默认执行，可 REPL 手动调用
        # print_error_codes()
        # 模式切换，注释默认执行，可 REPL 手动触发
        # switch_gyro_range()
        # 模式切换，注释默认执行，可 REPL 手动触发
        # switch_accel_range()
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    bmi270.deinit()
    bmi270 = None
    print("Program exited")
