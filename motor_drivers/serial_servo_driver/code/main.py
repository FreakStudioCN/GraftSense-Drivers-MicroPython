# Python env   : MicroPython v1.23.0 on Raspberry Pi Pico
# -*- coding: utf-8 -*-        
# @Time    : 2025/1/3 下午11:00   
# @Author  : 李清水            
# @File    : main.py       
# @Description : 串口类实验，通过串口控制串口舵机LX-1501转动

# ======================================== 导入相关模块 =========================================

# 硬件相关的模块
from machine import UART, Pin
# 时间相关的模块
import time
# 导入串口舵机库
from serial_servo import SerialServo

# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================

# 计时装饰器，用于计算函数运行时间
def timed_function(f: callable, *args: tuple, **kwargs: dict) -> callable:
    """
    计时装饰器，用于计算并打印函数/方法运行时间。

    Args:
        f (callable): 需要传入的函数/方法
        args (tuple): 函数/方法 f 传入的任意数量的位置参数
        kwargs (dict): 函数/方法 f 传入的任意数量的关键字参数

    Returns:
        callable: 返回计时后的函数
    """
    myname = str(f).split(' ')[1]

    def new_func(*args: tuple, **kwargs: dict) -> any:
        t: int = time.ticks_us()
        result = f(*args, **kwargs)
        delta: int = time.ticks_diff(time.ticks_us(), t)
        print('Function {} Time = {:6.3f}ms'.format(myname, delta / 1000))
        return result

    return new_func

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试信息
print("FreakStudio : Using UART to control LX-1501 servo")

# 创建串口对象，设置波特率为115200
uart_servo = UART(0, 115200)
# 初始化uart对象，数据位为8，无校验位，停止位为1
# 设置串口超时时间为5ms
uart_servo.init(bits=8, parity=None, stop=1, tx=0, rx=1, timeout=5)

# 创建串口舵机对象
servo = SerialServo(uart_servo)

# 设置GPIO 25为LED输出引脚，下拉电阻使能
led = Pin(25, Pin.OUT, Pin.PULL_DOWN)

# ========================================  主程序  ===========================================

# 立即移动舵机到指定位置
servo.move_servo_immediate(servo_id=1, angle=90.0, time_ms=1000)

# 获取舵机移动到指定位置后的角度和移动时间
angle, time = servo.get_servo_move_immediate(servo_id=1)
print(f"Servo ID: 1, Angle: {angle}, Time: {time}")