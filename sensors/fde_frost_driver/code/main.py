# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/7 下午5:30
# @Author  : hogeiha
# @File    : main.py
# @Description : FDE冰霜冰冻传感器数据读取与打印

# ======================================== 导入相关模块 =========================================

# 导入时间模块，用于延时
import time
# 导入FDE传感器驱动类
from fde_frost_sensor import FDEFrostSensor

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 等待3秒，确保系统稳定
time.sleep(3)
# 打印启动标识
print("FreakStudio: FDE Sensor Data Reading")
# 创建FDE传感器对象，参数：从机地址1，UART编号0，TX引脚16，RX引脚17
sensor = FDEFrostSensor(slave_addr=1, uart_id=0, tx_pin=16, rx_pin=17)

# ========================================  主程序  ============================================

# 校准值：校准空载电容值（当前注释，需要时可取消）
# sensor.fde_set_calibration(1)  

# 打印数据标题
print("=== FDE Sensor Real-time Data ===")

# 获取并打印温度值（扩大10倍，单位℃）
print(f"Temperature: {sensor.fde_temperature():.1f} °C")
# 获取并打印C1电容值（单位pF）
print(f"C1 Capacitance: {sensor.fde_c1():.3f} pF")
# 获取并打印C2电容值（单位pF）
print(f"C2 Capacitance: {sensor.fde_c2():.3f} pF")
# 获取并打印C3电容值（单位pF）
print(f"C3 Capacitance: {sensor.fde_c3():.3f} pF")
# 获取并打印C2与C3电容之和（单位pF）
print(f"C2+C3 Sum: {sensor.fde_c2_c3_sum():.3f} pF")
# 获取并打印空载电容预值（单位pF）
print(f"No-load Capacitance Preset: {sensor.fde_no_load_cap()}")
# 获取并打印硬件版本号
print(f"Hardware Version: {sensor.fde_hw_ver()}")
# 获取并打印固件版本号
print(f"Firmware Version: {sensor.fde_fw_ver()}")
# 打印结束分隔线
print("============================")
