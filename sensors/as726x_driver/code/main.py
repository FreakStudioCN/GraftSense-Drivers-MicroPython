# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : Roberto Colistete Jr.
# @File    : main.py
# @Description : RP2040 test entry for AS7263 spectral sensor
# @License : MIT

# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin
import time

from as726x import AS726X
from as726x import AS726X_GAIN_16X
from as726x import AS726X_I2C_ADDR
from as726x import AS726X_ONE_SHOT_READING_ALL_CHANNELS
from as726x import SENSORTYPE_AS7263

# ======================================== 全局变量 ============================================

I2C_ID = 0
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100000
SENSOR_ADDR = AS726X_I2C_ADDR
INTEGRATION_TIME = 50
READ_INTERVAL_MS = 2000
last_read_ms = 0

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: AS7263 spectral sensor RP2040 test")

try:
    i2c = I2C(I2C_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
    print("I2C bus initialized: id=%d scl=%d sda=%d freq=%d" % (I2C_ID, I2C_SCL_PIN, I2C_SDA_PIN, I2C_FREQ))

    devices = i2c.scan()
    print("I2C scan result: %s" % [hex(device) for device in devices])
    if SENSOR_ADDR not in devices:
        raise RuntimeError("AS7263 not found at address 0x%02X" % SENSOR_ADDR)

    sensor = AS726X(i2c, SENSOR_ADDR)
    sensor_type = sensor.get_sensor_type()
    if sensor_type != SENSORTYPE_AS7263:
        raise RuntimeError("Unexpected AS726x device id 0x%02X" % sensor_type)

    sensor.set_gain(AS726X_GAIN_16X)
    sensor.set_integration_time(INTEGRATION_TIME)
    sensor.set_measurement_mode(AS726X_ONE_SHOT_READING_ALL_CHANNELS)
    print("AS7263 initialized: addr=0x%02X gain=16X integration=%d mode=one-shot" % (SENSOR_ADDR, INTEGRATION_TIME))
except Exception as init_error:
    print("Initialization failed: %s" % init_error)
    raise

# ========================================  主程序  ============================================

try:
    while True:
        now = time.ticks_ms()
        if time.ticks_diff(now, last_read_ms) >= READ_INTERVAL_MS:
            try:
                sensor.take_one_shot_sync_measurement()
                data = sensor.get_calibrated_rstuvw()
                print("AS7263 calibrated R=%.4f S=%.4f T=%.4f U=%.4f V=%.4f W=%.4f" % data)
            except OSError as read_error:
                print("I2C read failed: %s" % read_error)
            except Exception as read_error:
                print("Sensor read failed: %s" % read_error)
            last_read_ms = now
        time.sleep_ms(50)
except KeyboardInterrupt:
    print("Program interrupted by user")
finally:
    try:
        sensor.deinit()
    except Exception:
        pass
    print("Program exited")
