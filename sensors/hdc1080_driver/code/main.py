# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 00:00
# @Author  : Mike Causer
# @File    : main.py
# @Description : HDC1080 温湿度传感器测试代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

from machine import Pin
from machine import I2C
import time
from time import sleep_ms
from hdc1080 import HDC1080

# ======================================== 全局变量 ============================================

# 目标设备 I2C 地址（HDC1080 固定为 0x40）
_TARGET_ADDR = 0x40
# 期望设备 ID（HDC1080 固定为 0x1050）
_EXPECTED_DEVICE_ID = 0x1050

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 等待系统稳定
time.sleep(3)
print("FreakStudio: Testing HDC1080 Temperature & Humidity Sensor ...")

# 初始化 I2C 总线
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)

# I2C 总线扫描
devices = i2c.scan()
if len(devices) == 0:
    raise RuntimeError("No I2C device found")
print("I2C devices found: %s" % [hex(d) for d in devices])

# 检查目标地址是否存在
if _TARGET_ADDR not in devices:
    raise RuntimeError("Device not found at expected address 0x%02X" % _TARGET_ADDR)

# 初始化传感器
hdc = HDC1080(i2c)

# 芯片 ID 验证
device_id = hdc.device_id()
if device_id == _EXPECTED_DEVICE_ID:
    print("Device found: HDC1080 (ID: 0x%04X)" % device_id)
else:
    print("Device not found: unexpected ID 0x%04X" % device_id)

# 配置传感器参数
hdc.config(humid_res=14, temp_res=14, mode=0, heater=False)

# 检查设备就绪并打印序列号
if hdc.check():
    print("Found HDC1080 with serial number %d" % hdc.serial_number())

# ========================================  主程序  ===========================================

try:
    while True:
        # 每 500ms 读取并打印温湿度值
        print("%.2f C, %.2f %%RH" % (hdc.temperature(), hdc.humidity()))
        sleep_ms(500)

except KeyboardInterrupt:
    print("Program interrupted by user")
except (OSError, RuntimeError) as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    hdc.deinit()
    del hdc
    del i2c
    print("Program exited")
