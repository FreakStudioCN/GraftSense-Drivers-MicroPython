# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/1/19 下午5:33
# @Author  : hogeiha
# @File    : main.py
# @Description : 串口心率检测模块固件

# ======================================== 导入相关模块 =========================================

import time
from data_flow_processor import DataFlowProcessor
from ad8232 import AD8232
from machine import UART, Pin, Timer
from ecg_module_cmd import AD8232_DataFlowProcessor
from ecg_signal_processor import ECGSignalProcessor

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: Serial Port Heart Rate Detection Module Started")
# 串口实例
uart1 = UART(1, baudrate=115200, tx=Pin(8), rx=Pin(9))
# 数据帧构建实例
processordata = DataFlowProcessor(uart1)
# AD8232硬件驱动实例
ad8232=AD8232(adc_pin=27, loff_plus_pin=0, loff_minus_pin=1,sdn_pin=2)
# ecg信号滤波处理 心率计算
edg_signal = ECGSignalProcessor(AD8232=ad8232, fs=100.0)
# 模块串口协议接收，功能解析
ad8232_processor = AD8232_DataFlowProcessor(DataFlowProcessor=processordata,AD8232=ad8232,ECGSignalProcessor=edg_signal)
# 启动模块定时器
ad8232_processor.ECGSignalProcessor.start()

# ========================================  主程序  ============================================
