# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/12 下午4:12
# @Author  : hogeiha
# @File    : main.py
# @Description : CCS811传感器测试 读取eCO2和TVOC数据 配置驱动模式 软件重置传感器

# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin, SoftI2C
import time
from ccs811 import CCS811

# ======================================== 全局变量 ============================================

# 自动识别传感器地址，定义全局目标地址列表（支持多地址，单个也用[]）
TARGET_CCS811_ADDRS = [0x5A, 0x5B]
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 100000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: CCS811 sensor test - read eCO2 and TVOC data, configure drive mode, software reset sensor")

# I2C初始化（兼容I2C/SoftI2C）
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 开始扫描I2C总线上的设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 检查I2C设备扫描结果
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# 遍历地址列表初始化目标传感器
sensor = None  # 初始化传感器对象占位符
for device in devices_list:
    if device in TARGET_CCS811_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 自动识别并初始化对应传感器
            sensor = CCS811(i2c=i2c_bus, addr=device)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未找到目标设备，抛出异常
    raise Exception("No target sensor device found in I2C bus")

# ========================================  主程序  ============================================

try:
    # 初始化CCS811传感器
    sensor.setup()
    time.sleep(2)  # Wait for stabilization after initialization

    # 检查APP是否有效
    app_valid = sensor.app_valid()
    print(f"\nAPP validity: {app_valid}")

    # 检查传感器是否存在错误
    has_error = sensor.check_for_error()
    print(f"Sensor error status: {has_error}")

    # 获取传感器基线值
    baseline = sensor.get_base_line()
    print(f"Sensor baseline value: 0x{baseline:04X}")

    # 修改驱动模式为1秒/次
    print("\nSet drive mode to 1 second per reading...")
    sensor.set_drive_mode(1)
    time.sleep(1)

    # 循环读取eCO2和TVOC数据（读取5次）
    print("\nStart reading sensor data (5 times):")
    for i in range(5):
        co2 = sensor.read_eCO2()
        time.sleep(2)  # Wait according to drive mode
        tvoc = sensor.read_tVOC()
        print(f"Reading {i+1} - eCO2: {co2} ppm, TVOC: {tvoc} ppb")
        time.sleep(2)  # Wait according to drive mode

    # 执行传感器软件重置
    print("\nPerform sensor software reset...")
    sensor.reset()
    time.sleep(2)

    # 重置后重新初始化并读取一次数据
    print("\nRe-initialize after reset...")
    sensor.setup()
    time.sleep(2)
    co2 = sensor.read_eCO2()
    tvoc = sensor.read_tVOC()
    print(f"Reading after reset - eCO2: {co2} ppm, TVOC: {tvoc} ppb")

except ValueError as e:
    print(f"Runtime error: {e}")
except Exception as e:
    print(f"Unknown error: {e}")
