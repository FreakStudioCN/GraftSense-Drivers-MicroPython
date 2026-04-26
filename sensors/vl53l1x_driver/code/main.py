# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 下午2:30
# @Author  : hogeiha
# @File    : main.py
# @Description : 使用VL53L1X激光测距传感器进行距离测量

# ======================================== 导入相关模块 =========================================

# 从machine模块导入I2C类，用于硬件I2C通信
from machine import I2C
# 从vl53l1x模块导入VL53L1X类，用于控制VL53L1X激光测距传感器
from vl53l1x import VL53L1X
# 导入time模块，用于延时和睡眠
import time

# ======================================== 全局变量 ============================================

# 定义目标传感器地址列表（VL53L1X默认I2C地址为0x29，支持多地址，单个也用列表）
TARGET_SENSOR_ADDRS = [0x29]

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 启动后等待3秒，确保系统稳定
time.sleep(3)
# 打印启动提示（纯英文短句）
print("FreakStudio: VL53L1X Distance Measurement")

# 初始化硬件I2C总线0（Raspberry Pi Pico的GPIO4=SDA, GPIO5=SCL）
i2c_bus = I2C(0)

# 扫描I2C总线上的所有设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 判断是否扫描到任何I2C设备
if len(devices_list) == 0:
    # 未发现任何设备，退出程序
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    # 打印发现的设备数量
    print("i2c devices found:", len(devices_list))

# 初始化传感器对象占位符
sensor = None
# 遍历扫描到的设备地址
for device in devices_list:
    # 检查当前地址是否在目标地址列表中
    if device in TARGET_SENSOR_ADDRS:
        # 打印匹配到的十六进制地址
        print("I2c hexadecimal address:", hex(device))
        try:
            # 尝试使用该地址初始化VL53L1X传感器
            sensor = VL53L1X(i2c=i2c_bus,address=device)
            print("Sensor initialization successful")
            # 初始化成功，退出循环
            break
        except Exception as e:
            # 初始化失败，打印错误信息并继续尝试下一个地址
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未在总线中找到任何目标传感器地址，抛出异常
    raise Exception("No target sensor device found in I2C bus")

# ========================================  主程序  ============================================

# 无限循环，持续读取并打印距离值
while True:
    # 读取当前距离（单位：毫米）
    distance_mm = sensor.read()
    # 打印距离值
    print("range: mm ", distance_mm)
    # 延时50毫秒，控制采样频率约20Hz
    time.sleep_ms(50)