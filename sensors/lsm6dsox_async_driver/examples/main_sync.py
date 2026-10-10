# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : 测试 LSM6DSOX 六轴IMU驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import I2C, Pin
from lsm6dsox import LSM6DSOX

# ======================================== 全局变量 ============================================
# LSM6DSOX 默认 I2C 地址
LSM6DSOX_I2C_ADDR = 0x6A
# LSM6DSOX WHO_AM_I 期望值
LSM6DSOX_CHIP_ID = 0x6C
# LSM6DSOX WHO_AM_I 寄存器地址
LSM6DSOX_WHO_AM_I_REG = 0x0F
# 打印间隔（ms）
PRINT_INTERVAL = 2000
# 上次打印时间戳
last_print_time = 0
lsm = None


# ======================================== 功能函数 ============================================
def switch_gyro_range():
    """
    切换陀螺仪量程到 ±2000 dps（模式切换，默认注释调用，可 REPL 手动触发）
    Switch gyro range to +/-2000 dps (mode switch, commented by default, can be triggered from REPL).
    """
    lsm.gyro_range = lsm.RANGE_2000_DPS
    print("Gyro range switched to RANGE_2000_DPS")


def switch_accel_range():
    """
    切换加速度量程到 ±16g（模式切换，默认注释调用，可 REPL 手动触发）
    Switch acceleration range to +/-16g (mode switch, commented by default, can be triggered from REPL).
    """
    lsm.acceleration_range = lsm.RANGE_16G
    print("Accel range switched to RANGE_16G")


def switch_hpf():
    """
    切换高通滤波器模式（模式切换，默认注释调用，可 REPL 手动触发）
    Switch high-pass filter mode (mode switch, commented by default, can be triggered from REPL).
    """
    lsm.high_pass_filter = lsm.HPF_DIV100
    print("High-pass filter switched to HPF_DIV100")


def print_high_rate_data():
    """
    打印高频实时数据（高频，默认注释调用，可 REPL 手动调用）
    Print high-rate realtime data (high frequency, commented by default, can be called from REPL).
    """
    acc_x, acc_y, acc_z = lsm.acceleration
    print("Accel: x=%.3f, y=%.3f, z=%.3f" % (acc_x, acc_y, acc_z))
    temp = lsm.temperature
    print("Temp: %.2f C" % temp)


# ======================================== 自定义类 ============================================
# 无自定义类，直接使用 lsm6dsox.LSM6DSOX

# ======================================== 初始化配置 ==========================================
# 等待硬件就绪
time.sleep(3)
print("FreakStudio: Testing LSM6DSOX 6-axis IMU driver")

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
if LSM6DSOX_I2C_ADDR not in devices:
    raise RuntimeError("LSM6DSOX not found at expected address 0x%02X" % LSM6DSOX_I2C_ADDR)
print("LSM6DSOX found at 0x%02X" % LSM6DSOX_I2C_ADDR)

# 读取并验证 WHO_AM_I 芯片 ID
chip_id = i2c.readfrom_mem(LSM6DSOX_I2C_ADDR, LSM6DSOX_WHO_AM_I_REG, 1)[0]
if chip_id != LSM6DSOX_CHIP_ID:
    raise RuntimeError("Unexpected LSM6DSOX chip ID: expected 0x%02X, got 0x%02X" % (LSM6DSOX_CHIP_ID, chip_id))
print("LSM6DSOX chip ID verified: 0x%02X" % chip_id)

# 创建 LSM6DSOX 传感器实例
lsm = LSM6DSOX(i2c, address=LSM6DSOX_I2C_ADDR, debug=False)
print("LSM6DSOX initialized successfully")

# ========================================  主程序  ===========================================
last_print_time = time.ticks_ms()

try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
            # 读取加速度值（低频核心 API，保留自动执行）
            acc_x, acc_y, acc_z = lsm.acceleration
            print("Accel (m/s^2): x=%.3f, y=%.3f, z=%.3f" % (acc_x, acc_y, acc_z))

            # 读取陀螺仪值（低频核心 API，保留自动执行）
            gyro_x, gyro_y, gyro_z = lsm.gyro
            print("Gyro (rad/s): x=%.3f, y=%.3f, z=%.3f" % (gyro_x, gyro_y, gyro_z))

            # 读取温度值（低频核心 API，保留自动执行）
            temp = lsm.temperature
            print("Temperature: %.2f C" % temp)

            # 打印当前配置状态（低频状态查询，保留自动执行）
            print("Range: accel=%s, gyro=%s" % (lsm.acceleration_range, lsm.gyro_range))
            print("Data rate: accel=%s, gyro=%s" % (lsm.acceleration_data_rate, lsm.gyro_data_rate))
            print("HPF: %s" % lsm.high_pass_filter)
            print("---")
            last_print_time = current_time

        # print_high_rate_data()   # 高频函数，注释默认执行，可 REPL 手动调用
        # switch_gyro_range()      # 模式切换，注释默认执行，可 REPL 手动触发
        # switch_accel_range()     # 模式切换，注释默认执行，可 REPL 手动触发
        # switch_hpf()             # 模式切换，注释默认执行，可 REPL 手动触发
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    lsm.deinit()
    lsm = None
    print("Program exited")
