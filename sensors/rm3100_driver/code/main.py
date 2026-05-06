# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 07:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : RM3100 三轴地磁传感器驱动测试
# @License : MIT

# ======================================== 导入相关模块 =========================================

import math
import time
from machine import Pin, SoftI2C
from sensor_pack.bus_service import I2cAdapter
import rm3100mod
from rm3100mod import RM3100

# ======================================== 全局变量 ============================================

TARGET_SENSOR_ADDRS = [0x20, 0x21, 0x22, 0x23]
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400_000
MEASURE_AXIS = "XYZ"
UPDATE_RATE = 6

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: RM3100 geomagnetic sensor test")

# ========================================  主程序  ===========================================

if __name__ == '__main__':
    i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

    devices_list = i2c_bus.scan()
    print("START I2C SCANNER")

    if not devices_list:
        raise SystemExit("I2C scan found no devices")
    print("I2C devices found:", len(devices_list))

    sensor = None
    for device in devices_list:
        if device in TARGET_SENSOR_ADDRS:
            print("I2C address:", hex(device))
            try:
                sensor = RM3100(I2cAdapter(i2c_bus), address=device)
                print("Sensor initialization successful")
                break
            except Exception as e:
                print("Sensor init failed:", e)

    if sensor is None:
        raise SystemExit("No target sensor found on I2C bus")

    try:
        self_test = sensor.perform_self_test()
        self_test_ok = self_test[0] and self_test[1] and self_test[2]
        print("Self test result: %s  %s" % (self_test_ok, str(self_test)))
        print("Sensor id:", sensor.get_id())
        print(16 * "_")

        for axis in MEASURE_AXIS:
            print("%s axis cycle count: %d" % (axis, sensor.get_axis_cycle_count(axis)))

        sensor.start_measure(axis=MEASURE_AXIS, update_rate=UPDATE_RATE, single_mode=True)
        print("Is continuous meas mode:", sensor.is_continuous_meas_mode())
        wait_time_us = rm3100mod.get_conversion_cycle_time(UPDATE_RATE)
        time.sleep_us(wait_time_us)
        if sensor.is_data_ready():
            for axis in MEASURE_AXIS:
                print("%s axis magnetic field: %d" % (axis, sensor.get_meas_result(axis)))

        print("Continuous meas mode measurement")
        sensor.start_measure(axis=MEASURE_AXIS, update_rate=UPDATE_RATE, single_mode=False)
        print("Is continuous meas mode:", sensor.is_continuous_meas_mode())

        while True:
            time.sleep_us(wait_time_us)
            mag_field_comp = next(sensor)
            if mag_field_comp:
                mfs = math.sqrt(sum(v ** 2 for v in mag_field_comp))
                print("X: %d; Y: %d; Z: %d; mag field strength: %.2f" % (
                    mag_field_comp[0], mag_field_comp[1], mag_field_comp[2], mfs))

    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        sensor.deinit()
        print("Sensor deinitialized")
