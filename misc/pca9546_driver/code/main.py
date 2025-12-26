# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/08 15:00
# @Author  : 侯钧瀚
# @File    : mian.py
# @Description : 基于PCA9546ADR4通道I2C多路复用示例程序
# ======================================== 导入相关模块 =========================================
# 导入MicroPython标准库模块
from machine import Pin, I2C
# 导入时间模块
import time
# 导入pca9546模块
from pca9546adr import PCA9546ADR
# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================
# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Testing PCA9546ADR4 I2C Multiplexer Modules")

# 初始化 I2C 总线
i2c = I2C(1, scl=Pin(2), sda=Pin(3))

pca = PCA9546ADR(i2c)

# ========================================  主程序  ===========================================

while True:
    # 关闭所有通道
    pca.disable_all()
    # 打开通道0并打印iic地址
    pca.select_channel(0)
    print("0 address", i2c.scan())

    # 休眠4秒
    time.sleep(4)

    # 关闭所有通道
    pca.disable_all()
    # 打开通道1并打印iic地址
    pca.select_channel(1)
    print("1 address", i2c.scan())





