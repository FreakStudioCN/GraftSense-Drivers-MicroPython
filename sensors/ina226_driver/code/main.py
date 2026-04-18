# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/16 下午2:30
# @Author  : hogeiha
# @File    : main.py
# @Description : INA226 current/power sensor I2C scan and measurement example

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, SoftI2C
from sensor_pack_2.bus_service import I2cAdapter
import ina_ti

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# 显示分段标题
def show_header(info: str, width: int = 32):
    print(width * "-")
    print(info)
    print(width * "-")

# 微秒级延时
def my_sleep(delay_us: int):
    time.sleep_us(delay_us)

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

if __name__ == '__main__':
    # 启动前等待3秒，确保外设稳定
    time.sleep(3)
    # 打印调试标识
    print("FreakStudio: INA226 sensor initialization")

    # 自动识别传感器地址，定义全局目标地址列表（支持多地址，单个也用[]）
    TARGET_SENSOR_ADDRS = [0x40]  # INA226 默认地址

    # I2C初始化（兼容I2C/SoftI2C）
    i2c_bus = SoftI2C(sda=Pin(4), scl=Pin(5), freq=100000)

    # 开始扫描I2C总线上的设备
    devices_list: list[int] = i2c_bus.scan()
    print("START I2C SCANNER")

    # 检查I2C设备扫描结果
    if len(devices_list) == 0:
        print("No i2c device !")
        raise SystemExit("I2C scan found no devices, program exited")
    else:
        print("i2c devices found:", len(devices_list))

    # 遍历地址列表初始化目标传感器
    sensor = None  # 初始化传感器对象占位符
    for device in devices_list:
        if device in TARGET_SENSOR_ADDRS:
            print("I2c hexadecimal address:", hex(device))
            try:
                # 自动识别并初始化对应传感器
                adaptor = I2cAdapter(i2c_bus)
                sensor = ina_ti.INA226(adapter=adaptor, address=device, shunt_resistance=0.01)
                sensor.shunt_voltage_enabled = True
                sensor.max_expected_current = 2.0  # Ampere
                print("Sensor initialization successful")
                break
            except Exception as e:
                print(f"Sensor Initialization failed: {e}")
                continue
    else:
        # 未找到目标设备，抛出异常
        raise Exception("No target sensor device found in I2C bus")

# ========================================  主程序  ============================================

    # 测量循环次数
    cycles_count = 10

    # 手动测量模式
    show_header("INA226. Manual mode with settings")
    # 启动单次测量（非连续模式），执行校准
    sensor.start_measurement(continuous=False, enable_calibration=True)
    # 打印配置寄存器值
    print(f"configuration: {sensor.get_config()}")
    # 获取转换周期时间（微秒）
    wait_time_us = sensor.get_conversion_cycle_time()
    print(f"wait_time_us: {wait_time_us} us.")
    # 循环测量
    for _ in range(cycles_count):
        # 等待100毫秒
        time.sleep_ms(100)
        # 等待转换完成
        my_sleep(wait_time_us)
        # 获取数据状态
        ds = sensor.get_data_status()
        # 如果转换未就绪，跳过本次
        if not ds.conv_ready_flag:
            print(f"data status: {ds}")
            continue
        # 读取分流电压、总线电压、电流、功率
        shunt_v, bus_v, curr, pwr = sensor.get_shunt_voltage(), sensor.get_voltage(), sensor.get_current(), sensor.get_power()
        print(f"Shunt: {shunt_v} V;\tBus: {bus_v}\tCurrent: {curr}\tpower: {pwr}")
        # 禁止重复校准（每次手动触发测量时不再校准）
        sensor.start_measurement(continuous=False, enable_calibration=False)

    # 自动测量模式
    show_header("INA226. Automatic continuous mode")
    # 启动连续测量模式，并执行校准
    sensor.start_measurement(continuous=True, enable_calibration=True)
    # 打印配置寄存器值
    print(f"configuration: {sensor.get_config()}")
    # 迭代传感器数据（自动测量模式支持迭代）
    for data in sensor:
        # 等待转换完成
        my_sleep(wait_time_us)
        # 获取数据状态
        ds = sensor.get_data_status()
        # 如果转换未就绪，跳过本次
        if not ds.conv_ready_flag:
            print(f"data status: {ds}")
            continue
        # 打印测量数据、电流和功率
        print(f"data: {data}, current: {sensor.get_current()}, pwr: {sensor.get_power()}")
        # 延时100毫秒，避免阻塞IDE
        time.sleep_ms(100)