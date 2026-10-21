# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 AXP2101 PMU 驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from axp2101 import AXP2101, AXP2101_SLAVE_ADDRESS, XPOWERS_AXP2101_CHIP_ID

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 硬件引脚定义
SCL_PIN = 22
SDA_PIN = 21
I2C_FREQ = 400000
I2C_ID = 0

# 上电稳定延时
time.sleep(3)
print("FreakStudio: AXP2101 PMU driver test starting...")

# 初始化 I2C 总线
i2c = I2C(I2C_ID, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)

# I2C 地址扫描与验证
devices = i2c.scan()
print("I2C devices found:", [hex(d) for d in devices])
if AXP2101_SLAVE_ADDRESS not in devices:
    raise RuntimeError("AXP2101 not found at 0x%02X, scanned: %s" % (AXP2101_SLAVE_ADDRESS, [hex(d) for d in devices]))

device = None

# ========================================  主程序  ===========================================

try:
    # 创建 AXP2101 驱动实例
    device = AXP2101(i2c, addr=AXP2101_SLAVE_ADDRESS)

    # 验证芯片 ID
    chip_id = device.getChipID()
    print("AXP2101 chip ID: 0x%02X" % chip_id)
    if chip_id != XPOWERS_AXP2101_CHIP_ID:
        raise RuntimeError("Unexpected chip ID 0x%02X, expected 0x%02X" % (chip_id, XPOWERS_AXP2101_CHIP_ID))

    # 读取电池状态
    print("Battery connected:", device.isBatteryConnect())
    if device.isBatteryConnect():
        print("Battery voltage: %d mV" % device.getBattVoltage())
        print("Battery percent: %d%%" % device.getBatteryPercent())

    # 读取充电状态
    print("VBUS present:", device.isVbusIn())
    print("Charging:", device.isCharging())

    # 读取系统电源状态
    system_voltage = device.getSystemVoltage()
    print("System voltage: %d mV" % system_voltage)

    # 读取温度
    temp = device.getTemperature()
    print("PMU temperature: %.1f deg C" % temp)

    print("AXP2101 test completed successfully")

except Exception as e:
    print("AXP2101 test error:", e)

finally:
    if device is not None:
        device.deinit()
        print("AXP2101 deinitialized")
    device = None
