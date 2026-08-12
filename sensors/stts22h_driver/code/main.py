# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/08/11 00:00
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : Test STTS22H temperature sensor driver
# @License : MIT

# ==================== 导入相关模块 ====================

import time
from machine import I2C, Pin
from micropython_stts22h.stts22h import STTS22H

# ==================== 全局变量 ====================

I2C_BUS_ID = 1
I2C_SCL_PIN = 3
I2C_SDA_PIN = 2
I2C_FREQ = 400000

STTS22H_I2C_ADDR = 0x3C
STTS22H_CHIP_ID = 0xA0
STTS22H_WHOAMI_REG = 0x01

PRINT_INTERVAL_MS = 1000
last_print_time = 0

# ==================== 功能函数 ====================

# ==================== 自定义类 ====================

# ==================== 初始化配置 ====================

time.sleep(3)

print("FreakStudio: STTS22H driver class test")

# 初始化 I2C 总线
i2c = I2C(
    I2C_BUS_ID,
    sda=Pin(I2C_SDA_PIN),
    scl=Pin(I2C_SCL_PIN),
    freq=I2C_FREQ,
)
print("I2C initialized: sda=%d, scl=%d" % (I2C_SDA_PIN, I2C_SCL_PIN))

# 扫描 I2C 总线并确认目标地址存在
devices = i2c.scan()
print("I2C scan result:", [hex(address) for address in devices])
if not devices:
    raise RuntimeError("No I2C device found")
if STTS22H_I2C_ADDR not in devices:
    raise RuntimeError("Device not found at expected address")
print("Device found at 0x%02X" % STTS22H_I2C_ADDR)

# 读取 WHO_AM_I 寄存器确认芯片 ID
try:
    chip_id = i2c.readfrom_mem(STTS22H_I2C_ADDR, STTS22H_WHOAMI_REG, 1)[0]
except OSError as error:
    raise RuntimeError("Failed to read device ID") from error

if chip_id != STTS22H_CHIP_ID:
    message = "Unexpected device ID: 0x%02X" % chip_id
    raise RuntimeError(message)
print("Device ID verified: 0x%02X" % chip_id)

# 创建 STTS22H 驱动对象
sensor = STTS22H(i2c, address=STTS22H_I2C_ADDR)
print("STTS22H initialized successfully")
print("Output data rate: %s" % sensor.output_data_rate)
print("Main loop started")
last_print_time = time.ticks_ms()

# ====================  主程序  ====================

try:
    while True:
        current_time = time.ticks_ms()
        elapsed_time = time.ticks_diff(current_time, last_print_time)
        if elapsed_time >= PRINT_INTERVAL_MS:
            print("Temperature: %.2f C" % sensor.temperature)
            last_print_time = current_time
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as error:
    print("Hardware communication error: %s" % str(error))
except Exception as error:
    print("Unknown error: %s" % str(error))
finally:
    print("Cleaning up resources...")
    sensor.deinit()
    del sensor
    print("Program exited")
