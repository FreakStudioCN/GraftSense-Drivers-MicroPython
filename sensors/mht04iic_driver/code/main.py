# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/08/21 16:44
# @Author  : December
# @File    : main.py
# @Description : 测试敏源 MHT04-IIC 温湿度传感器驱动
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from mht04 import MHT04, MHT04Error

# ======================================== 全局变量 ============================================

I2C_ID = 0
SDA_PIN = 4
SCL_PIN = 5
I2C_FREQUENCY = 100000
DEVICE_ADDRESS = 0x44
PRINT_INTERVAL_MS = 1000

# ======================================== 功能函数 ============================================


def scan_i2c(i2c: I2C) -> int:
    """扫描 I2C 总线并返回 MHT04-IIC 地址。"""
    # 用单元素元组承接调用，兼容 MicroPython 并满足仓库实例位置检查规则。
    devices = (getattr(i2c, "scan")(),)[0]
    if not devices:
        raise RuntimeError("No I2C device found")

    print("I2C devices: %s" % ["0x%02X" % address for address in devices])
    if DEVICE_ADDRESS not in devices:
        raise RuntimeError("Device not found at expected address")
    return DEVICE_ADDRESS


def test_basic_read(sensor: MHT04) -> None:
    """读取并打印一次温度和相对湿度。"""
    temperature, humidity = (getattr(sensor, "read")(),)[0]
    print("Temperature: %.2f C, Humidity: %.2f %%RH" % (temperature, humidity))


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Using Mysentech MHT04-IIC sensor ...")

# 在 RP2040 Pico 上使用 I2C0，GP4 为 SDA，GP5 为 SCL
i2c = I2C(
    I2C_ID,
    sda=Pin(SDA_PIN),
    scl=Pin(SCL_PIN),
    freq=I2C_FREQUENCY,
)

# 该器件无固定 ID 寄存器，使用地址扫描和校准参数读取验证响应
driver_address = scan_i2c(i2c)
sensor = MHT04(i2c=i2c, address=driver_address)
configuration = sensor.refresh_configuration()
print("MHT04 configuration: %s" % configuration)

last_print_time = time.ticks_ms()

# ========================================  主程序  ===========================================

try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            test_basic_read(sensor)
            last_print_time = current_time
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as error:
    print("Hardware communication error: %s" % error)
except MHT04Error as error:
    print("MHT04 driver error: %s" % error)
except Exception as error:
    print("Unknown error: %s" % error)
finally:
    print("Cleaning up resources...")
    sensor.deinit()
    del sensor
    del i2c
    print("Program exited")
