# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/08 16:52
# @Author  : hogeiha
# @File    : main.py
# @Description : 测试SCD4X CO2/温湿度传感器驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

from machine import Pin, SoftI2C
from scd4x import SCD4X
import time

# ======================================== 全局变量 ============================================

TARGET_SENSOR_ADDRS = [0x62]
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 100_000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Using SCD4X CO2/temperature/humidity sensor ...")

# 初始化SoftI2C总线
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# 扫描I2C总线设备
devices_list = i2c_bus.scan()
print("START I2C SCANNER")
if len(devices_list) == 0:
    raise RuntimeError("I2C scan found no devices")
print("I2C devices found: %d" % len(devices_list))

# 遍历扫描结果，初始化目标传感器
sensor = None
for device in devices_list:
    if device in TARGET_SENSOR_ADDRS:
        print("I2C address: %s" % hex(device))
        sensor = SCD4X(i2c_bus=i2c_bus, address=device)
        print("Sensor initialization successful")
        break

if sensor is None:
    raise RuntimeError("No target sensor found on I2C bus")

# 打印序列号
print("SCD4X Serial Number: %s" % str(sensor.serial_number))

# 配置传感器参数
sensor.altitude = 100
sensor.temperature_offset = 2.0
sensor.self_calibration_enabled = True
sensor.persist_settings()

# 启动周期测量模式
sensor.start_periodic_measurement()
print("Start measuring...")

# ========================================  主程序  ===========================================

try:
    while True:
        if sensor.data_ready:
            co2 = sensor.CO2
            temp = sensor.temperature
            humi = sensor.relative_humidity
            print("CO2: %d ppm  Temp: %.2f C  RH: %.2f %%" % (co2, temp, humi))
        time.sleep(5)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    sensor.deinit()
    del sensor
    print("Program exited")
