# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/07 12:00
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : Test the Renesas HS3003 temperature and humidity sensor driver
# @License : MIT

# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin
import time

from hs3003 import HS3003

# ======================================== 全局变量 ============================================

HS3003_ADDR = 0x44
SAMPLE_INTERVAL_MS = 1000
last_sample_time = 0

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: Testing HS3003 driver module")

i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
devices = i2c.scan()
print("Devices found: %s" % [hex(device) for device in devices])

if not devices:
    raise RuntimeError("No I2C device found")
if HS3003_ADDR not in devices:
    raise RuntimeError("Device not found at expected address 0x%02X" % HS3003_ADDR)

sensor = HS3003(i2c, address=HS3003_ADDR)

# 该器件无固定 ID 寄存器，因此执行一次最小安全读取作为响应检查
try:
    temperature, humidity = sensor.measurements
except (OSError, RuntimeError) as error:
    raise RuntimeError("HS3003 did not respond to measurement read") from error

print("HS3003 responded successfully")
last_sample_time = time.ticks_ms()

# ========================================  主程序  ===========================================

try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_sample_time) >= SAMPLE_INTERVAL_MS:
            # 低频核心读取保留自动执行，每次只输出一条温湿度信息
            temperature, humidity = sensor.measurements
            print("T=%.2f C  RH=%.2f %%" % (temperature, humidity))

            last_sample_time = current_time

        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as error:
    print("Hardware communication error: %s" % error)
except Exception as error:
    print("Unknown error: %s" % error)
finally:
    print("Cleaning up resources...")
    sensor.deinit()
    del sensor
    del i2c
    print("Program exited")
