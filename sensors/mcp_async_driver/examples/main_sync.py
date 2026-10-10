# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/9 下午6:02
# @Author  : hogeiha
# @File    : main.py
# @Description : MER电子水尺传感器初始化、参数读取与实时数据循环采集程序

# ======================================== 导入相关模块 =========================================
# 导入MER电子水尺传感器驱动类
from mer import MER

# 导入时间模块，用于延时控制
import time

# ======================================== 全局变量 ============================================
# 传感器Modbus从机地址
SLAVE_ADDR = 1
# 使用的UART端口编号
UART_ID = 0
# UART发送引脚
TX_PIN = 16
# UART接收引脚
RX_PIN = 17

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================
time.sleep(3)
print("FreakStudio: MER Water Level Sensor Running")

# 实例化MER电子水尺传感器对象
sensor = MER(SLAVE_ADDR, UART_ID, TX_PIN, RX_PIN)
# 打印传感器初始化完成信息
print("=" * 50)
print("MER Electronic Water Level Sensor Initialized")
print("=" * 50)

# ========================================  主程序  ============================================
# 读取并打印设备基础只读信息
print("\n【Device Basic Info】")
# 读取传感器节点地址
print(f"Current Node Address: {sensor.read_node_address()}")
# 读取硬件版本号
print(f"Hardware Version: {sensor.read_hw_version()}")
# 读取固件版本号
print(f"Firmware Version: {sensor.read_fw_version()}")
# 读取设备唯一识别码
print(f"Device UID: {sensor.read_device_uid()}")

# 读取并打印传感器可读写配置参数
print("\n【Configuration Parameters】")
# 读取滤波次数参数
print(f"Filter Count: {sensor.read_filter_count()}")
# 读取低功耗模式使能状态
print(f"Low Power Enable: {sensor.read_low_power_enable()}")
# 读取参考液位1数值
print(f"Reference Level 1: {sensor.read_ref_level1()} mm")
# 读取参考液位2数值
print(f"Reference Level 2: {sensor.read_ref_level2()} mm")
# 读取参考液位3数值
print(f"Reference Level 3: {sensor.read_ref_level3()} mm")

# 修改配置参数示例代码，按需启用
# 修改滤波次数为10次
# sensor.write_filter_count(10)
# 开启低功耗工作模式
# sensor.write_low_power_enable(1)
# 修改传感器节点地址为2
# sensor.write_node_address(2)

# 传感器校准操作示例代码，按需启用
# print("\n【Start Calibration】")
# sensor.write_ref_level1(30)
# sensor.write_calib_switch(1)
# time.sleep(1)
# sensor.write_ref_level2(70)
# sensor.write_calib_switch(2)
# time.sleep(1)
# sensor.write_ref_level3(100)
# sensor.write_calib_switch(3)
# print("Calibration Completed")

# 循环读取传感器实时采集数据
print("\n【Real-time Data Reading Loop】")
while True:
    # 读取液位数据
    level = sensor.read_level()
    # 读取温度数据
    temp = sensor.read_temp()
    # 读取电容数据
    cap = sensor.read_capacitance()
    # 读取比值数据
    ratio = sensor.read_ratio()
    # 读取频率数据
    freq = sensor.read_frequency()

    # 打印实时采集的各类数据
    print(f"Level: {level} mm | Temperature: {temp} ℃ | Capacitance: {cap} pF | Ratio: {ratio} | Frequency: {freq} MHz")
    # 每隔1秒读取一次数据
    time.sleep(1)
