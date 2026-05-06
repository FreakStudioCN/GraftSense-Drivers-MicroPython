# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 18:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 SI1145 紫外线/可见光/红外光/接近度传感器驱动的代码
# @License : MIT


# ======================================== 导入相关模块 =========================================

# 导入 MicroPython 硬件 I2C 与引脚控制模块
from machine import I2C, Pin

# 导入 SI1145 驱动模块
from si1145 import SI1145

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
i2c_freq = 400000

# SI1145 默认 I2C 地址
si1145_addr = 0x60

# 数据打印间隔时间（毫秒）
print_interval = 1000

# 上次打印时间戳（毫秒）
last_print_time = 0


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ==========================================

# 等待系统和传感器上电稳定
time.sleep(3)

# 打印程序功能提示
print("FreakStudio: Testing SI1145 UV/light/proximity sensor driver")

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

# 检查 SI1145 是否在 I2C 总线上
if si1145_addr not in devices:
    raise RuntimeError("SI1145 not found at address 0x%02X" % si1145_addr)

# 打印 SI1145 地址确认
print("SI1145 found at address: 0x%02X" % si1145_addr)

# 创建 SI1145 传感器对象
sensor = SI1145(i2c=i2c, addr=si1145_addr)

# 打印初始化完成提示
print("SI1145 initialized successfully")


# ========================================  主程序  ===========================================

try:
    while True:
        # 获取当前时间戳
        current_time = time.ticks_ms()

        # 检查是否到达打印间隔
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 读取紫外线指数
            uv_index = sensor.read_uv

            # 读取可见光强度
            visible = sensor.read_visible

            # 读取红外光强度
            ir = sensor.read_ir

            # 读取接近度值
            proximity = sensor.read_prox

            # 打印测量结果
            print("UV: %.2f, Visible: %d, IR: %d, Proximity: %d" % (
                uv_index, visible, ir, proximity
            ))

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
