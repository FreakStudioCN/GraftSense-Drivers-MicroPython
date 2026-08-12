# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : Peter Hinch
# @File    : main.py
# @Description : Main test entry for the BNO055 MicroPython driver
# @License : MIT

# ======================================== 导入相关模块 =========================================

import machine
import time
from bno055 import BNO055

# ======================================== 全局变量 ============================================

I2C_ID = 0
SDA_PIN = 4
SCL_PIN = 5
I2C_FREQ = 100000
BNO055_ADDR = 0x29
CHIP_ID_REG = 0x00
CHIP_ID_VAL = 0xA0
READ_INTERVAL_MS = 2000
USE_SOFT_I2C = False

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: BNO055 9-axis IMU sensor test")

if USE_SOFT_I2C:
    i2c = machine.SoftI2C(sda=machine.Pin(SDA_PIN), scl=machine.Pin(SCL_PIN), timeout=1000)
else:
    i2c = machine.I2C(I2C_ID, sda=machine.Pin(SDA_PIN), scl=machine.Pin(SCL_PIN), freq=I2C_FREQ)

sensor = None
last_print_time = 0

try:
    devices = i2c.scan()
    print("I2C scan: %s" % [hex(device) for device in devices])
    if BNO055_ADDR not in devices:
        raise RuntimeError("BNO055 not found at 0x%02X" % BNO055_ADDR)

    chip_id = i2c.readfrom_mem(BNO055_ADDR, CHIP_ID_REG, 1)[0]
    if chip_id != CHIP_ID_VAL:
        raise RuntimeError("Chip ID mismatch: expected 0x%02X, got 0x%02X" % (CHIP_ID_VAL, chip_id))
    print("BNO055 detected at 0x%02X with chip ID 0x%02X" % (BNO055_ADDR, chip_id))

    sensor = BNO055(i2c, address=BNO055_ADDR, crystal=True, debug=False)
    print("BNO055 initialized successfully")
    print("Current mode: %d" % sensor.mode())
    print("Crystal: %s" % ("External" if sensor.external_crystal() else "Internal"))

    cal = sensor.cal_status()
    print("Calibration S:%d G:%d A:%d M:%d" % (cal[0], cal[1], cal[2], cal[3]))
    print("Temperature: %d C" % sensor.temperature())
    print("Euler: %.3f, %.3f, %.3f" % sensor.euler())
    print("Quaternion: %.3f, %.3f, %.3f, %.3f" % sensor.quaternion())
    print("Accel: %.3f, %.3f, %.3f" % sensor.accel())
    print("Gyro: %.3f, %.3f, %.3f" % sensor.gyro())
    print("Mag: %.3f, %.3f, %.3f" % sensor.mag())
    print("Linear accel: %.3f, %.3f, %.3f" % sensor.lin_acc())
    print("Gravity: %.3f, %.3f, %.3f" % sensor.gravity())
    last_print_time = time.ticks_ms()
except OSError as exc:
    print("I2C initialization error: %s" % exc)
    raise
except Exception as exc:
    print("BNO055 initialization error: %s" % exc)
    raise

# ========================================  主程序  ============================================

try:
    while True:
        now = time.ticks_ms()
        if time.ticks_diff(now, last_print_time) >= READ_INTERVAL_MS:
            cal = sensor.cal_status()
            print("Calibration S:%d G:%d A:%d M:%d" % (cal[0], cal[1], cal[2], cal[3]))
            print("Temperature: %d C" % sensor.temperature())
            print("Euler: %.3f, %.3f, %.3f" % sensor.euler())
            print("Quaternion: %.3f, %.3f, %.3f, %.3f" % sensor.quaternion())
            print("Accel: %.3f, %.3f, %.3f" % sensor.accel())
            print("Gyro: %.3f, %.3f, %.3f" % sensor.gyro())
            print("Mag: %.3f, %.3f, %.3f" % sensor.mag())
            print("Linear accel: %.3f, %.3f, %.3f" % sensor.lin_acc())
            print("Gravity: %.3f, %.3f, %.3f" % sensor.gravity())
            last_print_time = now
        time.sleep_ms(50)
except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as exc:
    print("I2C read error: %s" % exc)
except Exception as exc:
    print("Sensor read error: %s" % exc)
finally:
    print("Cleaning up resources")
    if sensor is not None:
        sensor.deinit()
    print("Program exited")
