# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/1/19 下午5:33
# @Author  : hogeiha
# @File    : main.py
# @Description : 串口心率检测模块使用示例

# ======================================== 导入相关模块 =========================================

from machine import UART, Pin, Timer
import micropython
import time
from data_flow_processor import DataFlowProcessor
from ad8232_uart import AD8232_DataFlowProcessor

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: Serial Port Heart Rate Detection Module Usage Example")
# 模块通信串口1
uart1 = UART(1, baudrate=115200, tx=Pin(8), rx=Pin(9))
# 波形输出串口0
uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1), bits=8, parity=None, stop=1)
# 数据帧构建实例
processordata = DataFlowProcessor(uart1)
# AD8232串口模块指令发送解析实例
ad8232 = AD8232_DataFlowProcessor(processordata)

# ========================================  主程序  ============================================

# 启动ad8232
ad8232.control_ad8232_start_stop(True)
# 打开主动上报
ad8232.set_active_output(True)

while True:
    # 打开主动上报，自动定时器解析更新实例属性
    raw_val_dc = ad8232.ecg_value
    filtered_val = ad8232.filtered_ecg_value

    # 主动上报不包括导联状态，需要查询返回，查询后返回，同时更新属性
    lead_status = ad8232.query_off_detection_status()
    heart_rate = ad8232.heart_rate

    # 输出波形信息，串口绘图仪查看
    uart_str = f"{raw_val_dc},{filtered_val}\r\n"
    uart.write(uart_str.encode('utf-8'))  # 显式编码，避免截断
    # 终端打印心率 ，导联状态
    print(f"lead_status：{lead_status},heart_rate：{heart_rate}\r\n")
    time.sleep_ms(10)
