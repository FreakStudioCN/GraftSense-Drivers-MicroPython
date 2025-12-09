# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:11
# @Author  : ben0i0d
# @File    : main.py
# @Description : tas755c测试文件

# ======================================== 导入相关模块 =========================================

# 导入硬件相关模块
import time
from machine import UART, Pin
# 导入第三方驱动模块
from tas_755c_eth import TAS_755C_ETH

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# 上电延时3s
time.sleep(3)
# 打印调试信息
print("FreakStudio:tas755c test")

# 初始化 UART 通信（按硬件实际接线调整 TX/RX）
uart0 = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
# 创建 HC14_Lora 实例
tas = TAS_755C_ETH(uart0)
# 切换AT模式
tas.enter_command_mode()

print(tas.get_mqtt_pubtopic())
tas.enter_data_mode()

# ========================================  主程序  ===========================================
while True:
    if tas._uart.any():
        print(tas._uart.read().decode('utf-8'))