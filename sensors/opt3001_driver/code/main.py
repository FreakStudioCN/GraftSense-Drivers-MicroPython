# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 07:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : OPT3001 环境光传感器驱动测试
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, SoftI2C
from sensor_pack_2.bus_service import I2cAdapter
from opt3001mod import OPT3001

# ======================================== 全局变量 ============================================

TARGET_SENSOR_ADDRS = [0x44, 0x45]
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100_000

# ======================================== 功能函数 ============================================

def show_header(info: str, width: int = 32):
    print(width * "-")
    print(info)
    print(width * "-")

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: OPT3001 light sensor test")

# ========================================  主程序  ============================================

if __name__ == '__main__':
    i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

    devices_list = i2c_bus.scan()
    print("START I2C SCANNER")

    if not devices_list:
        raise SystemExit("I2C scan found no devices")
    print("i2c devices found:", len(devices_list))

    sensor = None
    for device in devices_list:
        if device in TARGET_SENSOR_ADDRS:
            print("I2C address:", hex(device))
            try:
                sensor = OPT3001(I2cAdapter(i2c_bus), device)
                print("Sensor initialization successful")
                break
            except Exception as e:
                print("Sensor init failed:", e)

    if sensor is None:
        raise SystemExit("No target sensor found on I2C bus")

    try:
        _id = sensor.get_id()
        print("manufacturer id: 0x%x; device id: 0x%x" % (_id.manufacturer_id, _id.device_id))

        show_header("Single measurement mode! Manual start! Auto range selection by sensor!")
        sensor.long_conversion_time = False
        sensor.start_measurement(continuously=False, lx_range_index=10)
        cycle_time = sensor.get_conversion_cycle_time()
        print("cycle time ms:", cycle_time)
        print(sensor.read_config_from_sensor(return_value=True))

        for _ in range(10):
            time.sleep_ms(cycle_time + 50)
            ds = sensor.get_data_status()
            if ds.conversion_ready:
                print(sensor.get_measurement_value(value_index=1))
            else:
                print("Data not ready for reading!")
            sensor.start_measurement(continuously=False, lx_range_index=12)

        show_header("Automatic measurement start! Auto range selection by sensor!")
        sensor.long_conversion_time = True
        sensor.start_measurement(continuously=True, lx_range_index=12)
        print(sensor.read_config_from_sensor(return_value=True))
        cycle_time = sensor.get_conversion_cycle_time()
        print("cycle time ms: %d; increased conversion time: %s" % (cycle_time, sensor.long_conversion_time))

        for _ in range(100):
            time.sleep_ms(cycle_time)
            ds = sensor.get_data_status()
            if ds.conversion_ready:
                print(sensor.get_measurement_value(value_index=1))
            else:
                print("Data not ready for reading!")
    finally:
        sensor.deinit()
        print("Sensor deinitialized")
