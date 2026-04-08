# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : alankrantas
# @File    : calling.py
# @Description : SIM7600模块通话功能示例，实现拨打电话、挂断、接听、查询状态、设置音量

# ======================================== 导入相关模块 =========================================

# 导入SIM7600核心类
from sim7600 import SIM7600

# 从sim7600模块导入通话功能类
from sim7600.calling import Calling

# 从machine模块导入UART和Pin类，用于硬件引脚和串口配置
from machine import UART, Pin

# 导入time模块，用于延时操作
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 延时3秒，确保SIM7600模块完成初始化
time.sleep(3)
# 打印通话模块初始化完成提示信息
print("FreakStudio: SIM7600 calling module initialized successfully")
# 配置UART0串口，波特率115200，TX引脚16，RX引脚17（适配Raspberry Pi Pico）
uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17))
# 实例化SIM7600核心类，传入配置好的UART对象
sim7600 = SIM7600(uart)
# 实例化通话功能类，传入SIM7600核心实例
calling = Calling(sim7600)


# ========================================  主程序  ============================================

# 拨打电话，指定目标手机号码
calling.make_call("+8619524162376")

# 挂断当前通话
calling.hang_up()

# 接听来电
calling.answer_call()

# 查询当前通话状态
status = calling.call_status()
# 打印通话状态信息
print(status)

# 设置通话音量，参数为5（音量范围通常1-10）
calling.set_call_volume(5)
