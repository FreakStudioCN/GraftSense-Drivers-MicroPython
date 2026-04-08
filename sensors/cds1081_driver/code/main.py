# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : hogeiha
# @File    : main.py
# @Description : CDS1081雨量传感器数据读取与阈值配置

# ======================================== 导入相关模块 =========================================

import time
from cds1081 import CDS1081

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 等待系统稳定
time.sleep(3)
# 输出初始化完成提示
print("FreakStudio: CDS1081 sensor initialized")

# 创建CDS1081传感器对象，指定从机地址、UART ID、TX引脚和RX引脚
sensor = CDS1081(slave_addr=1, uart_id=0, tx_pin=16, rx_pin=17)

# 设置电容校准值，扩大1000倍，对应6pF
sensor.set_calibration(6000)
# 设置报警阈值
sensor.set_alarm_threshold(40000)
# 设置清除阈值
sensor.set_clear_threshold(20000)

# ========================================  主程序  ============================================

# 无限循环读取传感器数据
while True :
    # 打印节点地址
    print("Node address:", sensor.get_node_address())
    # 打印雨量状态
    print("Rain status:", sensor.get_rain_status())
    # 打印温度值
    print("Temperature:", sensor.get_temperature(), "C")
    # 打印电容值
    print("Capacitance:", sensor.get_capacitance(), "pF")
    # 打印Count0值
    print("Count0 value:", sensor.get_count0())
    # 打印校准理想值
    print("Calibration ideal value:", sensor.get_calibration_value(), "pF")
    # 打印报警阈值
    print("Alarm threshold:", sensor.get_alarm_threshold())
    # 打印清除阈值
    print("Clear threshold:", sensor.get_clear_threshold())