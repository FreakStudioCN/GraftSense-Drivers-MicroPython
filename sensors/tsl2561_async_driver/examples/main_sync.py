# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 下午
# @Author  : hogeiha
# @File    : main.py
# @Description : TSL2561 数字光照强度传感器读取示例

# ======================================== 导入相关模块 =========================================

from machine import Pin, SoftI2C
from tsl2561 import TSL2561, T_SLOW
import time

# ======================================== 全局变量 ============================================

# TSL2561 常见 I2C 地址列表
TARGET_SENSOR_ADDRS = [0x29, 0x39, 0x49]

# I2C 数据线连接到 Pico GPIO4
I2C_SDA_PIN = 4

# I2C 时钟线连接到 Pico GPIO5
I2C_SCL_PIN = 5

# I2C 通信频率设置为 100kHz
I2C_FREQ = 100000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: TSL2561 lux sensor")

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
    # 判断当前地址是否为 TSL2561 常见地址
    if device in TARGET_SENSOR_ADDRS:
        print("I2C hexadecimal address:", hex(device))

        try:
            # 创建 TSL2561 传感器对象
            sensor = TSL2561(i2c_bus, addr=device)

            # 设置 402ms 积分时间和 1 倍增益
            sensor.set_timing_gain(T_SLOW, gain=False)

            # 读取并打印传感器 ID
            sensor_id = sensor.get_id()
            print("Sensor initialization successful")
            print("TSL2561 ID:", sensor_id)
            break
        except Exception as e:
            print("Sensor initialization failed:", e)
            continue

# 未找到目标传感器时退出程序
if sensor is None:
    raise SystemExit("No TSL2561 device found")

# 等待第一次积分完成
time.sleep(0.5)

# ========================================  主程序  ============================================

try:
    while True:
        # 读取原始双通道光照数据
        raw_channel_0, raw_channel_1 = sensor.read_raw()

        # 读取换算后的光照强度
        lux = sensor.get_lumi()

        # 打印英文格式的光照数据
        print(
            "CH0: {}  CH1: {}  Lux: {:.2f}".format(
                raw_channel_0,
                raw_channel_1,
                lux,
            )
        )

        # 每秒读取一次传感器
        time.sleep(1)
except KeyboardInterrupt:
    # 中断时关闭传感器以降低功耗
    sensor.set_power_up(False)

    # 打印停止提示
    print("Measurement stopped")
