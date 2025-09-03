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

def user_callback(data: tuple) -> None:
    """
    用户自定义的回调函数，用于处理采集到的摇杆数据。

    Args:
        data (tuple): 包含摇杆的X轴、Y轴电压值和按键状态的元组，格式为 (x_value, y_value, sw_value)。

    Returns:
        None
    """
    # 声明全局变量
    global ball

    # 打印摇杆数据值
    x_value, y_value, sw_value = data
    print("X: {:.2f}, Y: {:.2f}, Switch: {}".format(x_value, y_value, sw_value))

    # 移动小球
    ball.move_ball(x_value,y_value)

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 延时3s等待设备上电完毕
time.sleep(3)
# 打印调试信息
print("FreakStudio : reading the voltage value of Joystick experiment")

# 创建摇杆实例，使用ADC0-GP26、ADC1-GP27作为Y轴和X轴
joystick = Joystick(vrx_pin=0, vry_pin=1, freq=10, callback=user_callback)

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