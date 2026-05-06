# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 07:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : SGP40/SGP41 空气质量传感器驱动测试
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, SoftI2C
from sensor_pack_2.bus_service import I2cAdapter
from sgp4Xmod import SGP4X

# ======================================== 全局变量 ============================================

TARGET_SENSOR_ADDRS = [0x59]
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100_000
SENSOR_ID = 0          # 0=SGP40, 1=SGP41

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: SGP40/SGP41 air quality sensor test")

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
                sensor = SGP4X(I2cAdapter(i2c_bus), address=device, sensor_id=SENSOR_ID)
                print("Sensor initialization successful")
                break
            except Exception as e:
                print("Sensor init failed:", e)

    if sensor is None:
        raise SystemExit("No target sensor found on I2C bus")

    try:
        sn = sensor.get_id()
        print("Serial number: 0x%04X 0x%04X 0x%04X" % (sn.word_0, sn.word_1, sn.word_2))

        result = sensor.execute_self_test()
        print("Self test: %s (0x%04X)" % ("PASS" if result == 0xD400 else "FAIL", result))

        if SENSOR_ID == 1:
            print("Conditioning SGP41 for 10s...")
            for _ in range(10):
                val = sensor.execute_conditioning(rel_hum=50, temperature=25)
                print("Conditioning VOC raw:", val.VOC)
                time.sleep_ms(1000)

        print("Starting measurement loop (Ctrl+C to stop)...")
        while True:
            val = sensor.measure_raw_signal(rel_hum=50, temperature=25)
            if SENSOR_ID == 1:
                print("VOC raw: %d  NOx raw: %d" % (val.VOC, val.NOx))
            else:
                print("VOC raw:", val.VOC)
            time.sleep_ms(1000)

    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        sensor.deinit()
        print("Sensor deinitialized")
