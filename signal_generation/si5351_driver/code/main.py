# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/08 10:21
# @Author  : 侯钧瀚
# @File    : main.py
# @Description : 基于SI5351芯片的时钟信号发生模块示例
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : CC BY-NC 4.0

# ======================================== 导入相关模块 =========================================
#导入引脚控制模块
import machine
#导入 SI5351 驱动模块
from silicon5351 import SI5351_I2C
# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

crystal = 25e6     # crystal frequency
mul = 15           # 15 * 25e6 = 375 MHz PLL frequency
freq = 3.0e6       # output frequency with an upper limit 200MHz
quadrature = True  # lower limit for quadrature is 375MHz / 128
invert = False     # invert option ignored when quadrature is true

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

i2c = machine.I2C(1, scl=machine.Pin(7), sda=machine.Pin(6))

# ========================================  主程序  ===========================================

si = SI5351_I2C(i2c, crystal=crystal)
si.setup_pll(pll=0, mul=mul)
si.init_clock(output=0, pll=0)
si.init_clock(output=1, pll=0, quadrature=quadrature, invert=invert)
si.set_freq_fixedpll(output=0, freq=freq)
si.set_freq_fixedpll(output=1, freq=freq)
si.enable_output(output=0)
si.enable_output(output=1)
print(f'done freq={freq} mul={mul} quadrature={quadrature} invert={invert}')








