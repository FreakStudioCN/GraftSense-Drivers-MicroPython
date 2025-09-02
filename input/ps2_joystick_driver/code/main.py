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
from joystick import Joystick, user_callback

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 延时3s等待设备上电完毕
time.sleep(3)
# 打印调试信息
print("FreakStudio : reading the voltage value of Joystick experiment")

# 创建摇杆实例，使用ADC0-GP26、ADC1-GP27作为Y轴和X轴，GP28 作为按键
joystick = Joystick(vrx_pin=0, vry_pin=1, vsw_pin=22, freq=10, callback=user_callback)

# ========================================  主程序  ===========================================

# 启动摇杆数据采集
joystick.start()
# 运行一段时间，观察摇杆的状态
time.sleep(30)
# 停止数据采集
joystick.stop()
# 获取最后一次读取的摇杆值
x_val, y_val, sw_val = joystick.get_values()
print("Final Joystick values: X = {:.2f}, Y = {:.2f}, Switch = {}".format(x_val, y_val, sw_val))