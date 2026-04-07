# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/3 上午10:30
# @Author  : hogeiha
# @File    : main.py
# @Description : MSE土壤温湿度传感器数据读取与配置示例程序

# ======================================== 导入相关模块 =========================================

import time
from mse_soil_sensor import MSESoilSensor

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def read_all():
    """
    读取并打印传感器所有寄存器数据

    Args:
        无

    Raises:
        无

    Notes:
        调用驱动类中所有只读方法，并将结果格式化输出到控制台。

    ==========================================
    Read and print all sensor register data

    Args:
        None

    Raises:
        None

    Notes:
        Call all read-only methods of driver class and format output to console.
    """
    # 打印数据分隔线
    print("=" * 50)
    # 打印从机地址
    print(f"Sensor data (Addr: {sensor.read_node_address()})")
    # 打印温度值
    print(f"Temperature        : {sensor.read_temperature()} C")
    # 打印电容值
    print(f"Capacitance        : {sensor.read_capacitance()} pF")
    # 打印电容中心值
    print(f"Capacitance center : {sensor.read_cap_center()} pF")
    # 打印电容量程
    print(f"Capacitance range  : {sensor.read_cap_range()} pF")
    # 打印滤波次数
    print(f"Filter count       : {sensor.read_filter_count()}")
    # 打印平均窗口大小
    print(f"Average window     : {sensor.read_avg_window_size()}")
    # 打印温补系数A
    print(f"Temp comp A        : {sensor.read_temp_comp_A()}")
    # 打印温补系数B
    print(f"Temp comp B        : {sensor.read_temp_comp_B()}")
    # 打印硬件版本
    print(f"Hardware version   : {sensor.read_hw_version()}")
    # 打印固件版本
    print(f"Firmware version   : {sensor.read_firmware_version()}")
    # 打印设备UID
    print(f"Device UID         : {sensor.read_device_uid()}")
    # 打印结束分隔线
    print("=" * 50)

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 等待3秒确保串口稳定
time.sleep(3)
# 打印启动提示信息
print("FreakStudio: MSE soil sensor test start")

# 创建传感器实例
sensor = MSESoilSensor(
    slave_addr=1,
    baudrate=9600,
    uart_id=0,
    tx_pin=16,
    rx_pin=17
)

# ========================================  主程序  ============================================

# 判断是否作为主程序运行
if __name__ == "__main__":
    # sensor.write_filter_count(20)      # 设置滤波次数
    # sensor.write_temp_comp_A(0.5)      # 设置温度补偿A
    # 写入温度补偿系数B
    sensor.write_temp_comp_B(0.5) 
    
    # 主循环：每隔2秒读取一次所有数据
    while True:
        read_all()
        time.sleep(2)