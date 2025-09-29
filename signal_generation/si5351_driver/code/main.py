# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/08 10:00
# @Author  : 侯钧瀚
# @File    : mian.py
# @Description : silicon5351时钟示例 for MicroPython
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : CC BY-NC 4.0

# ======================================== 导入相关模块 =========================================

#导入micropython自带库
import machine
#导入时间模块
import time
#导入silicon5351
from silicon5351 import SI5351_I2C

# ======================================== 全局变量 ============================================

crystal = 25e6     # 晶振频率 25 MHz
mul = 15           # PLL 倍频系数 (25MHz * 15 = 375 MHz)
freq = 2.0e6       # 输出频率 2 MHz（最大 200 MHz）
quadrature = True  # 正交输出标志（最低输出频率 = PLL / 128）
invert = False     # 反相输出标志（四相模式下忽略）

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Use silicon5351 to output clock signals.")
i2c = machine.I2C(1, scl=machine.Pin(7), sda=machine.Pin(6), freq = 100000)
# 初始化 SI5351 芯片
si = SI5351_I2C(i2c, crystal=crystal)
# 配置 PLL0 = 375 MHz
si.setup_pll(pll=0, mul=mul)
# 初始化输出通道 0 和 1，使用 PLL0
si.init_clock(output=0, pll=0)
si.init_clock(output=1, pll=0, quadrature=quadrature, invert=invert)
# 设置输出频率为 2 MHz（基于固定 PLL）
si.set_freq_fixedpll(output=0, freq=freq)
si.set_freq_fixedpll(output=1, freq=freq)

# ========================================  主程序  ===========================================
# 打开输出 0 和 1
si.enable_output(output=0)
si.enable_output(output=1)
print(f'done freq={freq} mul={mul} quadrature={quadrature} invert={invert}')
# 保持输出 20 秒
time.sleep(20)
# 关闭输出 0




