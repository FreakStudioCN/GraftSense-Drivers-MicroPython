# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/04/22 14:15
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 GP2Y0E03 数字红外测距传感器驱动的代码
# @License : MIT


# ======================================== 导入相关模块 =========================================

# 导入 MicroPython 硬件 I2C 与引脚控制模块
from machine import I2C, Pin

# 导入 GP2Y0E03 传感器驱动类
from gp2y0e03 import GP2Y0E03

# 导入时间控制模块
import time


# ======================================== 全局变量 ============================================

# I2C 总线编号
i2c_id = 0

# I2C 数据引脚编号
i2c_sda_pin = 4

# I2C 时钟引脚编号
i2c_scl_pin = 5

# I2C 通信频率（Hz）
i2c_freq = 100000

# GP2Y0E03 默认 I2C 地址
gp2y0e03_addr = 0x40

# 数据打印间隔时间（毫秒）
print_interval = 500

# 上次打印时间戳（毫秒）
last_print_time = 0


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ==========================================

# 等待系统和传感器上电稳定
time.sleep(3)

# 打印程序功能提示
print("FreakStudio: Testing GP2Y0E03 distance sensor driver")

# 初始化硬件 I2C 总线
i2c = I2C(
    i2c_id,
    sda=Pin(i2c_sda_pin),
    scl=Pin(i2c_scl_pin),
    freq=i2c_freq,
)

# 扫描 I2C 总线设备
devices = i2c.scan()

# 检查扫描结果是否为空
if not devices:
    raise RuntimeError("No I2C devices found on bus")

# 打印 I2C 设备扫描结果
print("I2C devices found: %s" % [hex(addr) for addr in devices])

# 检查 GP2Y0E03 是否在 I2C 总线上
if gp2y0e03_addr not in devices:
    raise RuntimeError("GP2Y0E03 not found at address 0x%02X" % gp2y0e03_addr)

# 打印 GP2Y0E03 地址确认
print("GP2Y0E03 found at address: 0x%02X" % gp2y0e03_addr)

# 创建 GP2Y0E03 传感器对象
sensor = GP2Y0E03(i2c, address=gp2y0e03_addr)

# 打印当前距离量程移位值
print("Shift: %d" % sensor._shift)


# ========================================  主程序  ===========================================

try:
    while True:
        # 获取当前时间戳
        current_time = time.ticks_ms()

        # 检查是否到达打印间隔
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 读取原始距离值
            raw = sensor.read(raw=True)

            # 读取厘米距离值
            distance = sensor.read()

            # 打印测量结果
            print("Raw: %d, Distance: %.2f cm" % (raw, distance))

            # 更新上次打印时间
            last_print_time = current_time

        # 短暂延时避免 CPU 占用过高
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    # 释放传感器对象
    del sensor
    # 释放 I2C 对象
    del i2c
    print("Program exited")
