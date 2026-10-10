# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : Mika Tuupola
# @File    : main.py
# @Description : 测试 IP5306 电源管理驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from ip5306 import IP5306

# ======================================== 全局变量 ============================================

# I2C 总线引脚配置（根据实际接线修改）
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4

# 设备 I2C 地址
IP5306_I2C_ADDR = 0x75

# 打印间隔常量
last_print_time = 0
PRINT_INTERVAL_MS = 2000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电稳定延时
time.sleep(3)

print("FreakStudio: Testing IP5306 battery level driver...")

# 初始化 I2C 总线实例
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))

# I2C 总线扫描验证
print("Scanning I2C bus...")
devices = i2c.scan()
if len(devices) == 0:
    raise RuntimeError("No I2C device found on bus")
print("Found I2C devices at: %s" % str([hex(d) for d in devices]))

# 验证目标设备地址
if IP5306_I2C_ADDR not in devices:
    raise RuntimeError("IP5306 not found at expected address 0x%02X" % IP5306_I2C_ADDR)
print("IP5306 device found at address 0x%02X" % IP5306_I2C_ADDR)

# 初始化驱动实例
device = IP5306(i2c, address=IP5306_I2C_ADDR)

# 读取电量状态寄存器，确认设备可通信
initial_level = device.level
print("IP5306 initial battery level: %d%%" % initial_level)

# ========================================  主程序  ===========================================

last_print_time = time.ticks_ms()

try:
    while True:
        # 获取当前时间
        current_time = time.ticks_ms()

        # 按周期打印电池电量
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            # 读取电池电量百分比
            battery_level = device.level
            print("Battery level: %d%%" % battery_level)
            last_print_time = current_time

        # 主循环延时
        time.sleep_ms(500)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    device.deinit()
    del device
    print("Program exited")
