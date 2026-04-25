# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 下午
# @Author  : FreakStudio
# @File    : main.py
# @Description : VEML7700 数字环境光传感器读取示例

# ======================================== 导入相关模块 =========================================

from machine import Pin, SoftI2C
from veml7700 import VEML7700
import time

# ======================================== 全局变量 ============================================

# VEML7700 默认 I2C 地址
TARGET_SENSOR_ADDRS = [0x10]

# I2C 数据线连接到 Pico GPIO4
I2C_SDA_PIN = 4

# I2C 时钟线连接到 Pico GPIO5
I2C_SCL_PIN = 5

# I2C 通信频率设置为 100kHz
I2C_FREQ = 100000

# 环境光积分时间设置为 100ms
INTEGRATION_TIME = 100

# 环境光增益设置为 1/8 倍
SENSOR_GAIN = 1 / 8

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: VEML7700 lux sensor")

# 初始化软件 I2C 总线
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# 扫描 I2C 总线设备
devices_list = i2c_bus.scan()
print("START I2C SCANNER")

# 判断是否扫描到 I2C 设备
if len(devices_list) == 0:
    print("No i2c device")
    raise SystemExit("I2C scan found no devices")

# 打印扫描到的 I2C 设备数量
print("I2C devices found:", len(devices_list))

# 初始化传感器对象占位符
sensor = None

# 遍历所有扫描到的 I2C 地址
for device in devices_list:
    # 判断当前地址是否为 VEML7700 默认地址
    if device in TARGET_SENSOR_ADDRS:
        print("I2C hexadecimal address:", hex(device))

        try:
            # 创建 VEML7700 传感器对象
            sensor = VEML7700(
                address=device,
                i2c=i2c_bus,
                it=INTEGRATION_TIME,
                gain=SENSOR_GAIN,
            )

            # 打印初始化成功提示
            print("Sensor initialization successful")
            break
        except Exception as e:
            print("Sensor initialization failed:", e)
            continue

# 未找到目标传感器时退出程序
if sensor is None:
    raise SystemExit("No VEML7700 device found")

# 等待第一次积分完成
time.sleep(0.2)

# ========================================  主程序  ============================================

try:
    while True:
        # 读取换算后的环境光强度
        lux = sensor.read_lux()

        # 打印英文格式的环境光强度
        print("Lux: {} lx".format(lux))

        # 每秒读取一次传感器
        time.sleep(1)
except KeyboardInterrupt:
    # 打印停止提示
    print("Measurement stopped")
