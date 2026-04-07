# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/3 下午2:30
# @Author  : FreakStudio
# @File    : main.py
# @Description : WS61水浸传感器数据采集主程序

# ======================================== 导入相关模块 =========================================

import time
from wd61 import WS61Water

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 等待硬件稳定
time.sleep(3)
# 输出初始化提示（纯英文）
print("FreakStudio: WS61 Water Sensor Initialization")

# 创建传感器对象，配置从机地址、UART编号、TX和RX引脚
sensor = WS61Water(slave_addr=1, uart_id=0, tx_pin=16, rx_pin=17)
# 写入报警电容阈值（单位：pF）
sensor.write_alarm_threshold(7.5)
# 写入解除报警阈值（单位：pF）
sensor.write_release_threshold(7)

# ========================================  主程序  ============================================

# 主循环：打印所有可读取参数
while True:
    # 读取设备ID
    dev_id = sensor.read_device_id()
    # 读取485节点地址
    node_addr = sensor.read_485_node_address()
    # 读取报警电容阈值
    alarm_th = sensor.read_alarm_threshold()
    # 读取解除报警阈值
    release_th = sensor.read_release_threshold()
    # 读取实时电容值
    cap = sensor.read_capacitance()
    # 读取环境温度
    temp = sensor.read_temperature()
    # 读取水浸状态（1：有水报警，0：无水）
    status = sensor.read_water_status()
    
    # 格式化打印所有参数（输出纯英文）
    print("="*60)
    print(f"Device ID: {dev_id if dev_id is not None else 'Read failed'}")
    print(f"485 Node Address: {node_addr if node_addr is not None else 'Read failed'}")
    print(f"Alarm threshold: {alarm_th} pF" if alarm_th is not None else "Alarm threshold: Read failed")
    print(f"Release threshold: {release_th} pF" if release_th is not None else "Release threshold: Read failed")
    print(f"Capacitance: {cap} pF" if cap is not None else "Capacitance: Read failed")
    print(f"Temperature: {temp} C" if temp is not None else "Temperature: Read failed")
    print(f"Water status: {'Water alarm' if status == 1 else 'No water'}" if status is not None else "Water status: Read failed")
    print("="*60)
    
    # 延时1秒
    time.sleep(1)