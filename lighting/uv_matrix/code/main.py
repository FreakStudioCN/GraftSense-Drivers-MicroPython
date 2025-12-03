# MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/26 上午10:45
# @Author  : 缪贵成
# @File    : main.py
# @Description : uv紫外灯矩阵模块驱动测试文件  建议不要长时间全亮 如果有全亮需求就更换电阻，否则电路板会迅速升温导致意外后果

# ======================================== 导入相关模块 =========================================

import time
from uv_matrix import UVMatrix

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("Freak_studio:UV matrix test")
# 初始化 UVMatrix，假设控制引脚为 26，PWM 频率 1000Hz
uv = UVMatrix(pin=26, pwm_freq=1000)

# ========================================  主程序  ===========================================

print("status:", uv.get_state())

# 打开 UVMatrix（全亮）
uv.on()
print("UV is light full:", uv.get_state())
time.sleep(2)

# 半亮调节
uv.set_brightness(512)
print("UV PWM duty=512")
time.sleep(2)

# 关闭 UVMatrix
uv.off()
print("UV status:", uv.get_state())
time.sleep(2)

# 切换状态测试 toggle
uv.toggle()
print("UV toggle:", uv.get_state())
time.sleep(2)
uv.toggle()
print("UV toggle:", uv.get_state())