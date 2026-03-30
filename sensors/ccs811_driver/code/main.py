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

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: CCS811 sensor test - read eCO2 and TVOC data, configure drive mode, software reset sensor")
# 初始化I2C总线（适配Raspberry Pi Pico，I2C 0，SCL=Pin(5), SDA=Pin(4)）
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
#    i2c = SoftI2C(scl=Pin(5), sda=Pin(4), freq=100000)
# 扫描I2C总线上的设备并打印地址
print(f"I2C scanned device addresses: {[hex(addr) for addr in i2c.scan()]}")
# 创建CCS811传感器实例
ccs811 = CCS811(i2c)

# ========================================  主程序  ============================================

try:
    # 初始化CCS811传感器
    ccs811.setup()
    time.sleep(2)  # Wait for stabilization after initialization

    # 检查APP是否有效
    app_valid = ccs811.app_valid()
    print(f"\nAPP validity: {app_valid}")

    # 检查传感器是否存在错误
    has_error = ccs811.check_for_error()
    print(f"Sensor error status: {has_error}")

    # 获取传感器基线值
    baseline = ccs811.get_base_line()
    print(f"Sensor baseline value: 0x{baseline:04X}")

    # 修改驱动模式为1秒/次
    print("\nSet drive mode to 1 second per reading...")
    ccs811.set_drive_mode(1)
    time.sleep(1)

    # 循环读取eCO2和TVOC数据（读取5次）
    print("\nStart reading sensor data (5 times):")
    for i in range(5):
        co2 = ccs811.read_eCO2()
        time.sleep(2)  # Wait according to drive mode
        tvoc = ccs811.read_tVOC()
        print(f"Reading {i+1} - eCO2: {co2} ppm, TVOC: {tvoc} ppb")
        time.sleep(2)  # Wait according to drive mode

    # 执行传感器软件重置
    print("\nPerform sensor software reset...")
    ccs811.reset()
    time.sleep(2)

    # 重置后重新初始化并读取一次数据
    print("\nRe-initialize after reset...")
    ccs811.setup()
    time.sleep(2)
    co2 = ccs811.read_eCO2()
    tvoc = ccs811.read_tVOC()
    print(f"Reading after reset - eCO2: {co2} ppm, TVOC: {tvoc} ppb")

except ValueError as e:
    print(f"Runtime error: {e}")
except Exception as e:
    print(f"Unknown error: {e}")
