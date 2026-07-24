# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : FreakStudio
# @File    : main.py
# @Description : BMI160 6-axis IMU test entry
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin

from bmi160 import (
    ACCEL_RANGE_2G,
    ACCEL_RANGE_4G,
    ACCEL_RANGE_8G,
    ACCEL_RANGE_16G,
    AVERAGING,
    BANDWIDTH_25,
    BANDWIDTH_50,
    BANDWIDTH_100,
    BANDWIDTH_400,
    BMI160,
    FILTER,
    GYRO_NORMAL,
    GYRO_OSR2,
    GYRO_OSR4,
    GYRO_RANGE_125,
    GYRO_RANGE_250,
    GYRO_RANGE_500,
    GYRO_RANGE_1000,
    GYRO_RANGE_2000,
    NO_UNDERSAMPLE,
    UNDERSAMPLE,
)

# ======================================== 全局变量 ============================================

I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400000

BMI160_I2C_ADDR = 0x69
BMI160_WHO_AM_I_REG = 0x00
BMI160_WHO_AM_I_VAL = 0xD1

PRINT_INTERVAL = 2000
last_print_time = 0

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: BMI160 6-axis IMU test")

i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
print("I2C initialized: scl=%d, sda=%d, freq=%d" % (I2C_SCL_PIN, I2C_SDA_PIN, I2C_FREQ))

print("Scanning I2C bus...")
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("I2C devices found: %s" % [hex(device) for device in devices])

if BMI160_I2C_ADDR not in devices:
    raise RuntimeError("Device not found at expected address 0x%02X" % BMI160_I2C_ADDR)
print("Device found at 0x%02X" % BMI160_I2C_ADDR)

whoami_raw = i2c.readfrom_mem(BMI160_I2C_ADDR, BMI160_WHO_AM_I_REG, 1)
if whoami_raw[0] != BMI160_WHO_AM_I_VAL:
    raise RuntimeError("WHO_AM_I mismatch: expected 0x%02X, got 0x%02X" % (BMI160_WHO_AM_I_VAL, whoami_raw[0]))
print("WHO_AM_I verified: 0x%02X (BMI160 confirmed)" % whoami_raw[0])

bmi = BMI160(i2c, address=BMI160_I2C_ADDR, debug=False)
print("BMI160 driver initialized successfully")
last_print_time = time.ticks_ms()

print("--- Initial Configuration ---")
print("Acc range: %s" % bmi.acceleration_range)
print("Acc ODR: %s" % bmi.acceleration_output_data_rate)
print("Gyro range: %s" % bmi.gyro_range)
print("Gyro ODR: %s" % bmi.gyro_output_data_rate)
print("Gyro power mode: %s" % bmi.gyro_power_mode)
print("-----------------------------")

# ========================================  主程序  ============================================


def print_realtime_data(sensor) -> None:
    acc = sensor.acceleration
    gyr = sensor.gyro
    tmp = sensor.temperature
    print("  Acc (m/s^2): X=%.3f Y=%.3f Z=%.3f" % acc)
    print("  Gyro (deg/s): X=%.1f Y=%.1f Z=%.1f" % gyr)
    print("  Temp (C): %.2f" % tmp)


def change_acc_range(sensor, range_val) -> None:
    print("Setting acceleration range to %s ..." % str(range_val))
    sensor.acceleration_range = range_val
    print("  Current range: %s" % sensor.acceleration_range)


def change_gyro_range(sensor, range_val) -> None:
    print("Setting gyro range to %s ..." % str(range_val))
    sensor.gyro_range = range_val
    print("  Current range: %s" % sensor.gyro_range)


def change_acc_odr(sensor, odr_val) -> None:
    print("Setting acceleration ODR to %s ..." % str(odr_val))
    sensor.acceleration_output_data_rate = odr_val
    print("  Current ODR: %s" % sensor.acceleration_output_data_rate)


def change_gyro_odr(sensor, odr_val) -> None:
    print("Setting gyro ODR to %s ..." % str(odr_val))
    sensor.gyro_output_data_rate = odr_val
    print("  Current ODR: %s" % sensor.gyro_output_data_rate)


def debug_error_codes(sensor) -> None:
    print("--- Error Code Register ---")
    sensor.error_code()
    print("--- Power Mode Status ---")
    sensor.power_mode_status()


def test_config_walkthrough(sensor) -> None:
    print("=== Configuration Walkthrough ===")

    for range_value in (ACCEL_RANGE_2G, ACCEL_RANGE_4G, ACCEL_RANGE_8G, ACCEL_RANGE_16G):
        sensor.acceleration_range = range_value
        print("  Acc range set: %s" % sensor.acceleration_range)

    for odr in (BANDWIDTH_25, BANDWIDTH_100, BANDWIDTH_400):
        sensor.acceleration_output_data_rate = odr
        print("  Acc ODR set: %s" % sensor.acceleration_output_data_rate)

    sensor.acceleration_undersample = NO_UNDERSAMPLE
    print("  Acc undersample: %s" % sensor.acceleration_undersample)
    sensor.acceleration_undersample = UNDERSAMPLE
    print("  Acc undersample: %s" % sensor.acceleration_undersample)

    sensor.acceleration_bandwidth_parameter = FILTER
    print("  Acc bandwidth: %s" % sensor.acceleration_bandwidth_parameter)
    sensor.acceleration_bandwidth_parameter = AVERAGING
    print("  Acc bandwidth: %s" % sensor.acceleration_bandwidth_parameter)

    sensor.acceleration_output_data_rate = BANDWIDTH_100
    sensor.acceleration_range = ACCEL_RANGE_2G
    sensor.acceleration_undersample = NO_UNDERSAMPLE

    for range_value in (GYRO_RANGE_125, GYRO_RANGE_250, GYRO_RANGE_500, GYRO_RANGE_1000, GYRO_RANGE_2000):
        sensor.gyro_range = range_value
        print("  Gyro range set: %s" % sensor.gyro_range)

    for odr in (BANDWIDTH_50, BANDWIDTH_100, BANDWIDTH_400):
        sensor.gyro_output_data_rate = odr
        print("  Gyro ODR set: %s" % sensor.gyro_output_data_rate)

    for bandwidth in (GYRO_OSR4, GYRO_OSR2, GYRO_NORMAL):
        sensor.gyro_bandwidth_parameter = bandwidth
        print("  Gyro bandwidth: %s" % sensor.gyro_bandwidth_parameter)

    sensor.gyro_output_data_rate = BANDWIDTH_100
    sensor.gyro_range = GYRO_RANGE_2000
    print("=== Walkthrough Done ===")


def test_exception_scenarios(sensor) -> None:
    print("=== Exception Scenario Tests ===")

    checks = (
        ("Acc range invalid", lambda: setattr(sensor, "acceleration_range", 0xFF)),
        ("Acc ODR invalid", lambda: setattr(sensor, "acceleration_output_data_rate", 0xFF)),
        ("Gyro range invalid", lambda: setattr(sensor, "gyro_range", 0xFF)),
        ("Gyro ODR invalid", lambda: setattr(sensor, "gyro_output_data_rate", 0xFF)),
        ("Acc power mode invalid", lambda: sensor.acc_power_mode(0xFF)),
        ("Gyro power mode invalid", lambda: setattr(sensor, "gyro_power_mode", 0xFF)),
    )
    for label, action in checks:
        try:
            action()
            print("  FAIL: should have raised ValueError")
        except ValueError as exc:
            print("  OK: %s -> ValueError: %s" % (label, exc))

    print("=== Exception Tests Done ===")


try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
            acc = bmi.acceleration
            gyr = bmi.gyro
            tmp = bmi.temperature

            print("--- BMI160 Data ---")
            print("Acc (m/s^2): X=%.3f Y=%.3f Z=%.3f" % acc)
            print("Gyro (deg/s): X=%.1f Y=%.1f Z=%.1f" % gyr)
            print("Temp (C): %.2f" % tmp)
            print("-------------------")
            last_print_time = current_time

        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as exc:
    print("Hardware communication error: %s" % str(exc))
except Exception as exc:
    print("Unknown error: %s" % str(exc))
finally:
    print("Cleaning up resources...")
    bmi.deinit()
    del bmi
    print("Program exited")
