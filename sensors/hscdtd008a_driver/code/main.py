# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 下午5:30
# @Author  : goctaprog
# @File    : main.py
# @Description : HSCDTD008A磁力计传感器驱动与测试

# ======================================== 导入相关模块 =========================================

import time
import math
import sys
from machine import Pin, SoftI2C
import hscdtd008a
from sensor_pack.bus_service import I2cAdapter

# ======================================== 全局变量 ============================================

TARGET_SENSOR_ADDRS = [0x0C]          # HSCDTD008A的I2C地址
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400_000

# ======================================== 功能函数 ============================================

def show_state(sen: hscdtd008a.HSCDTD008A):
    # 打印待机模式标志
    print(f"in standby mode: {sensor.in_standby_mode()}; hi_dynamic_range: {sensor.hi_dynamic_range};")
    # 打印测量模式标志
    print(f"single meas mode: {sensor.is_single_meas_mode()}; continuous meas mod: {sensor.is_continuous_meas_mode()};")

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: HSCDTD008A magnetic sensor test")

# ========================================  主程序  ============================================

if __name__ == '__main__':
    i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

    devices_list: list[int] = i2c_bus.scan()
    print("START I2C SCANNER")

    if len(devices_list) == 0:
        print("No i2c device !")
        raise SystemExit("I2C scan found no devices, program exited")
    else:
        print("i2c devices found:", len(devices_list))

    sensor = None
    for device in devices_list:
        if device in TARGET_SENSOR_ADDRS:
            print("I2c hexadecimal address:", hex(device))
            try:
                adapter = I2cAdapter(i2c_bus)
                sensor = hscdtd008a.HSCDTD008A(adapter,device)
                print("Sensor initialization successful")
                break
            except Exception as e:
                print(f"Sensor Initialization failed: {e}")
                continue
    else:
        raise Exception("No target sensor device found in I2C bus")

    dly: int = 250
    max_cnt = 30
    print(f"Sensor id: {sensor.get_id()}")
    print(f"Offset_drift_values: {sensor.offset_drift_values}")
    print(16 * "_")
    show_state(sensor)
    print(16 * "_")
    test_result = sensor.perform_self_test()
    if not test_result:
        print("Sensor not pass self test!!! Broken or invalid sensor mode!!!")
        sys.exit(1)
    print("Sensor self test passed!")
    sensor.enable_temp_meas(True)
    print("Sensor temperature measurement!")
    print(16 * "_")
    show_state(sensor)
    print(16 * "_")
    cnt = 0
    while cnt < max_cnt:
        status = sensor.get_status()
        # 检查温度数据就绪标志 (STAT1寄存器bit3)
        if status[3]:
            temp = sensor.get_temperature()
            print(f"Sensor temperature: {temp} ℃")
            sensor.enable_temp_meas(True)
        else:
            print(f"status: {status}")
        time.sleep_ms(dly)
        cnt += 1

    print(16 * "_")
    show_state(sensor)
    print(16 * "_")
    print("Magnetic field measurement! Force mode!")
    cnt = 0
    sensor.start_measure(continuous_mode=False)
    while cnt < max_cnt:
        status = sensor.get_status()
        # 检查数据就绪或溢出标志
        if status[0] or status[1]:
            field = sensor.get_axis(-1)
            sensor.start_measure(continuous_mode=False)
            print(f"magnetic field component: X:{field[0]}; Y:{field[1]}; Z:{field[2]}")
        else:
            print(f"status: {status}")
        time.sleep_ms(dly)
        cnt += 1

    print("Magnetic field measurement! Periodical mode!")
    sensor.use_offset = True
    sensor.start_measure(continuous_mode=True)
    cnt = 0
    while cnt < max_cnt:
        status = sensor.get_status()
        if status[0]:
            field = sensor.get_axis(-1)
            # 计算磁场强度
            mag_field_strength = math.sqrt(sum(map(lambda val: val ** 2, field)))
            print(f"magnetic field component: X:{field[0]}; Y:{field[1]}; Z:{field[2]}; {mag_field_strength}")
        time.sleep_ms(dly)