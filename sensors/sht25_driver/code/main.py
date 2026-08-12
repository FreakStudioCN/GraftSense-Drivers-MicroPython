# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 19:10
# @Author  : Miceuz
# @File    : main.py
# @Description : SHT25 温湿度传感器驱动测试
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time

from machine import I2C, Pin

from sht25 import SHT25

# ======================================== 全局变量 ============================================

# I2C 总线配置
I2C_ID = 0
SDA_PIN = 4
SCL_PIN = 5
I2C_FREQ = 400_000

# SHT25 设备 I2C 地址
SHT25_ADDR = 0x40

# 温湿度数据打印间隔（毫秒）
PRINT_INTERVAL_MS = 2000

# ======================================== 功能函数 ============================================


def scan_i2c(i2c: object) -> object:
    """
    扫描 I2C 总线并返回已发现设备地址列表。
    Args:
        i2c (I2C): I2C 总线实例
    Returns:
        list: 设备地址列表
    """
    devices = (getattr(i2c, "scan")(),)[0]
    print("I2C devices found:", ["0x%02X" % addr for addr in devices])
    return devices


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电等待，确保传感器稳定
time.sleep(3)

print("FreakStudio: SHT25 temperature and humidity sensor test")

# 初始化 I2C 总线
i2c = I2C(
    I2C_ID,
    sda=Pin(SDA_PIN),
    scl=Pin(SCL_PIN),
    freq=I2C_FREQ,
)

# 扫描 I2C 总线，检查是否有设备连接
devices = scan_i2c(i2c)
if not devices:
    raise RuntimeError("No I2C device found on bus")

# 验证目标设备地址是否存在
if SHT25_ADDR not in devices:
    raise RuntimeError("SHT25 not found at address 0x%02X" % SHT25_ADDR)

print("SHT25 found at address 0x%02X" % SHT25_ADDR)

# 初始化传感器驱动实例
sensor = SHT25(i2c, address=SHT25_ADDR)
last_print_time = time.ticks_ms()

# 软复位传感器，恢复默认状态
sensor.reset()

# 通过读取用户寄存器验证通信（SHT25 无芯片 ID 寄存器，以用户寄存器读取作为连通性校验）
try:
    user_reg = sensor.read_user_register()
    print("SHT25 user register: 0x%02X (communication OK)" % user_reg)
except RuntimeError as e:
    raise RuntimeError("SHT25 communication verification failed") from e

# ========================================  主程序  ===========================================

last_print_time = 0

try:
    while True:
        current_time = time.ticks_ms()
        # 按固定间隔读取并打印温湿度数据
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            temperature = sensor.temperature_c()
            humidity = sensor.humidity()
            print("Temperature: %.2f C / Humidity: %.2f %%" % (temperature, humidity))
            last_print_time = current_time

        # 短延时降低 CPU 占用
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    # 释放传感器资源
    sensor.deinit()
    del sensor
    del i2c
    print("Program exited")
