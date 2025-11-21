# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/8/27 下午10:02   
# @Author  : 李清水            
# @File    : main.py       
# @Description : ADC类实验，读取摇杆两端电压

# ======================================== 导入相关模块 ========================================

# 导入时间相关模块
import time
# 导入摇杆驱动模块
from joystick import Joystick

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 延时3s等待设备上电完毕
time.sleep(3)
# 打印调试信息
print("FreakStudio : reading the voltage value of Joystick experiment")

# 创建摇杆实例，使用ADC0-GP27、ADC1-GP28作为Y轴和X轴
joystick = Joystick(vrx_pin=27, vry_pin=28, freq=10)

# ========================================  主程序  ===========================================

# 启动摇杆数据采集
joystick.start()
# 打印摇杆数据
try:
    while True:
        x_val, y_val, sw_val = joystick.get_values()
        print("Joystick values: X = {:.2f}, Y = {:.2f}, Switch = {}".format(x_val, y_val, sw_val))
        # 每 1 秒打印一次
        time.sleep(1)  
except KeyboardInterrupt:
    print("\n数据采集结束")
finally:
    joystick.stop()