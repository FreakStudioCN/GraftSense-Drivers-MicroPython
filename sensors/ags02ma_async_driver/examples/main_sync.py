# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/04/22 14:15
# @Author  : hogeiha
# @File    : main.py
# @Description : AGS02MA气体传感器读取示例


# ======================================== 导入相关模块 =========================================

import machine
import time
from ags02ma import AGS02MA


# ======================================== 全局变量 ============================================

# I2C数据引脚编号
I2C_SDA_PIN = 4

# I2C时钟引脚编号
I2C_SCL_PIN = 5

# AGS02MA需要低速I2C通信
I2C_FREQ = 20000

# 传感器读取间隔时间（秒）
READ_INTERVAL = 10

# 传感器上电预热等待时间（秒）
WARMUP_SECONDS = 120


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ===========================================

# 等待系统和传感器上电稳定
time.sleep(3)

# 打印程序功能提示
print("FreakStudio: AGS02MA gas sensor")

# 初始化软件I2C总线
i2c = machine.SoftI2C(
    scl=machine.Pin(I2C_SCL_PIN),
    sda=machine.Pin(I2C_SDA_PIN),
    freq=I2C_FREQ,
)

# 扫描I2C总线设备
devices = i2c.scan()

# 打印I2C设备扫描结果
print("Devices: {}".format(devices))

# 创建AGS02MA传感器对象
ags = AGS02MA(i2c)

# 读取固件版本
firmware_version = ags.firmware_version() & 0x0000FF

# 打印固件版本
print("Firmware version: {}".format(firmware_version))

# 打印传感器预热提示
print("Warmup for {} seconds".format(WARMUP_SECONDS))


# ========================================  主程序  ============================================

# 持续读取AGS02MA传感器数据
while True:

    # 捕获单次读取异常避免示例程序退出
    try:

        # 读取TVOC浓度值
        tvoc = ags.TVOC

        # 打印TVOC浓度值
        print("TVOC: {}".format(tvoc))

    # 读取TVOC失败时打印英文错误
    except RuntimeError as exc:
        print("TVOC read failed: {}".format(exc))

        # 打印TVOC原始调试数据
        print("TVOC raw: {}".format(ags.debug_read_raw(0x00)))

    # 捕获单次读取异常避免示例程序退出
    try:

        # 读取气敏电阻值
        gas_resistance = ags.gas_resistance

        # 打印气敏电阻值
        print("Gas resistance: {}".format(gas_resistance))

    # 读取气敏电阻失败时打印英文错误
    except RuntimeError as exc:
        print("Gas resistance read failed: {}".format(exc))

        # 打印气敏电阻原始调试数据
        print("Gas resistance raw: {}".format(ags.debug_read_raw(0x20)))

    # 等待下一次读取
    time.sleep(READ_INTERVAL)
