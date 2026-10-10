# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : alankrantas
# @File    : main.py
# @Description : SIM7600模块短信功能示例，实现短信模式配置、发送短信、查询所有短信

# ======================================== 导入相关模块 =========================================

# 导入SIM7600核心类
from sim7600 import SIM7600

# 从sim7600模块导入短信功能类
from sim7600.sms import SMS

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
# 打印短信模块初始化完成提示信息
print("FreakStudio: SIM7600 SMS module initialized successfully")
# 配置UART0串口，波特率115200，TX引脚16，RX引脚17（适配Raspberry Pi Pico）
uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17))
# 实例化SIM7600核心类，传入配置好的UART对象
sim7600 = SIM7600(uart)
# 实例化短信功能类，传入SIM7600核心实例
sms = SMS(sim7600)

# ========================================  主程序  ============================================

# 配置短信模式参数（gmgf=1，csmp=17,11,0,0，字符集IRA）
sms.set_sms_mode(gmgf=1, csmp="17,11,0,0", CSCS="IRA")
# 发送短信到指定号码，内容为Hello, world!
sms.send_sms("19524162399", "FreakStudio: SIM7600 SMS module initialized successfully")

# 再次配置短信模式参数（确保参数生效）
sms.set_sms_mode(gmgf=1, csmp="17,11,0,0", CSCS="IRA")

# 查询所有短信列表
sms.list_sms("ALL")
