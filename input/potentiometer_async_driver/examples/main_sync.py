# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/28 下午3:19
# @Author  : 缪贵成
# @File    : main.py
# @Description : 滑动变阻器测试文件

# ======================================== 导入相关模块 =========================================

import time
from machine import ADC
from potentiometer import Potentiometer

# ======================================== 全局变量 ============================================

interval = 0.5

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio:Sliding rheostat module testing")

# 滑动变阻器电压输出端接在 ADC0
adc = ADC(26)
pot = Potentiometer(adc)

# ========================================  主程序  ============================================

try:
    while True:
        # 获取当前状态字典
        state = pot.get_state()
        # 打印当前状态
        print(f"State: raw={state['raw']}, voltage={state['voltage']:.3f} V, ratio={state['ratio']:.3f}")
        # 等待下一次读取
        time.sleep(interval)

except KeyboardInterrupt:
    print("\nTest terminated by user.")
