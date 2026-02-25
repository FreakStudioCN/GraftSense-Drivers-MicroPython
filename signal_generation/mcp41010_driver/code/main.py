# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/11/4 下午8:52
# @Author  : 李清水
# @File    : main.py
# @Description : 使用AD9833芯片和MCP4725芯片生成DDS信号，幅度相位频率可调

# ======================================== 导入相关模块 =========================================

# 硬件相关的模块
from machine import I2C, Pin

# 时间相关的模块
import time

# 导入AD9833芯片驱动模块
from ad9833 import AD9833

# 导入MCP41010芯片驱动模块
from mcp41010 import MCP41010

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Using AD9833 and DS3502 to implement DDS signal generator")

# # 创建AD9833芯片实例，使用SPI0外设：MOSI-GP19、SCLK-GP18、CS-GP20
ad9833 = AD9833(sdo=19, clk=18, cs=20, fmclk=25, spi_id=0)
# # 创建MCP41010芯片实例，使用SPI0外设：MOSI-GP19、SCLK-GP18、CS-GP21
mcp41010 = MCP41010(clk_pin=18, cs_pin=21, mosi_pin=19, spi_id=0, max_value=255)

# ========================================  主程序  ===========================================

# 设置AD9833芯片的频率和相位
# 设置频率寄存器0和相位寄存器0的数据
ad9833.set_frequency(5000, 0)
ad9833.set_phase(0, 0, rads=False)
# 设置频率寄存器1和相位寄存器1的数据
ad9833.set_frequency(1300, 1)
ad9833.set_phase(180, 1, rads=False)
# 选择AD9833芯片的频率和相位
ad9833.select_freq_phase(0, 0)

# 设置MCP41010芯片的电位器值
mcp41010.set_value(125)

# 选择频率寄存器0和相位寄存器0，设置DDS信号发生器的输出模式为正弦波
ad9833.select_freq_phase(0, 0)
ad9833.set_mode("SIN")

# # 调节电位器值，观察DDS信号发生器的输出波形
# mcp41010.set_value(20)
#
# # 选择频率寄存器0和相位寄存器0，设置DDS信号发生器的输出模式为方波
# ad9833.select_freq_phase(0,0)
# ad9833.set_mode('SQUARE')
#
# # 选择频率寄存器0和相位寄存器0，设置DDS信号发生器的输出模式为频率减半的方波
# ad9833.select_freq_phase(0,0)
# ad9833.set_mode('SQUARE/2')
#
# # 选择频率寄存器0和相位寄存器0，设置DDS信号发生器的输出模式为三角波
# ad9833.select_freq_phase(0,0)
# ad9833.set_mode('TRIANGLE')
#
# # 选择频率寄存器1和相位寄存器1，设置DDS信号发生器的输出模式为三角波
# ad9833.select_freq_phase(1,1)
# ad9833.set_mode('TRIANGLE')
