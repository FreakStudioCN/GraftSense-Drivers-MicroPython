# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/11 07:39
# @Author  : mimingxuan
# @File    : main.py
# @Description : 测试 SHTC3 温湿度传感器驱动的示例代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from shtc3 import SHTC3, SHTC3Error

# ======================================== 全局变量 ============================================

# I2C 总线引脚配置（GPIO 编号，非物理引脚号）
# Raspberry Pi Pico 示例：SCL=GP5, SDA=GP4, I2C(0)
# ESP8266 D1 mini 示例：SCL=D1/GPIO5, SDA=D2/GPIO4
I2C_ID = 0
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100000

# SHTC3 传感器地址和 ID 验证常量
SENSOR_ADDR = 0x70
EXPECTED_SENSOR_ID = 0x0807  # SHTC3 产品 ID（Sensirion 数据手册）

# 传感器实例（初始化配置区中赋值）
sensor = None

# 主循环采样间隔（毫秒）
SAMPLE_INTERVAL_MS = 2000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Using SHTC3 temperature and humidity sensor ...")

# 创建 I2C 总线实例
i2c = I2C(I2C_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# I2C 总线扫描：检测设备是否连接
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus %d" % I2C_ID)

print("I2C devices found: %s" % [hex(addr) for addr in devices])

# 验证目标地址是否存在
if SENSOR_ADDR not in devices:
    raise RuntimeError("SHTC3 not found at address %s" % hex(SENSOR_ADDR))

# 创建 SHTC3 传感器实例
sensor = SHTC3(i2c, addr=SENSOR_ADDR)

# 读取传感器 ID 并与期望值比对
try:
    chip_id = sensor.read_id()
    print("SHTC3 ID: %s" % hex(chip_id))
    if chip_id == EXPECTED_SENSOR_ID:
        print("Device found: SHTC3 sensor verified successfully")
    else:
        # 部分批次可能存在不同 ID 值，仅提示警告，不阻止运行
        print("Device found: ID %s (expected %s), continuing anyway" % (hex(chip_id), hex(EXPECTED_SENSOR_ID)))
except SHTC3Error as err:
    raise RuntimeError("Sensor communication failed: %s" % err)

# ========================================  主程序  ===========================================

try:
    while True:
        try:
            temperature, humidity = sensor.measure()
            print("Temperature: %.2f C, Humidity: %.2f %%" % (temperature, humidity))
        except SHTC3Error as err:
            print("Measurement failed: %s" % err)
        time.sleep_ms(SAMPLE_INTERVAL_MS)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    if sensor is not None:
        sensor.deinit()
        del sensor
    print("Program exited")
