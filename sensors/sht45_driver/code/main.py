# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : Test SHT45 temperature and humidity sensor driver
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time

import sht45
from machine import I2C, Pin
from sht45 import SHT45

try:
    import micropython

    micropython.alloc_emergency_exception_buf(100)
except (ImportError, AttributeError):
    pass


# ======================================== 全局变量 ============================================

I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100000

_PRINT_INTERVAL_MS = 2000
_last_print_time = 0

# ======================================== 初始化配置 ==========================================


def test_all_precision_modes(sht):
    """
    Test all precision commands.
    """
    print("\n=== Testing All Precision Modes ===")
    modes = [
        (sht45.HIGH_PRECISION, "HIGH_PRECISION"),
        (sht45.MEDIUM_PRECISION, "MEDIUM_PRECISION"),
        (sht45.LOW_PRECISION, "LOW_PRECISION"),
    ]
    for mode_value, mode_name in modes:
        sht.temperature_precision = mode_value
        print("Precision set to: %s" % mode_name)
        time.sleep(0.5)
        temp, hum = sht.measurements
        print("  Temperature: %.2f C, Humidity: %.2f %%RH" % (temp, hum))
    sht.temperature_precision = sht45.HIGH_PRECISION
    print("Precision restored to: %s" % sht.temperature_precision)


def test_all_heater_settings(sht):
    """
    Test all heater command combinations.
    """
    print("\n=== Testing Heater Settings ===")
    powers = [
        (sht45.HEATER200mW, "HEATER200mW"),
        (sht45.HEATER110mW, "HEATER110mW"),
        (sht45.HEATER20mW, "HEATER20mW"),
    ]
    times = [
        (sht45.TEMP_1, "TEMP_1"),
        (sht45.TEMP_0_1, "TEMP_0_1"),
    ]
    for power_value, power_name in powers:
        for time_value, time_name in times:
            sht.heater_power = power_value
            sht.heat_time = time_value
            print("Heater: %s, Duration: %s" % (power_name, time_name))
            temp, hum = sht.measurements
            print("  Temperature: %.2f C, Humidity: %.2f %%RH" % (temp, hum))
            time.sleep(0.5)
    sht.heater_power = sht45.HEATER20mW
    sht.heat_time = sht45.TEMP_0_1
    sht.temperature_precision = sht45.HIGH_PRECISION
    print("Heater settings restored to default")


def test_invalid_params(sht):
    """
    Test parameter validation.
    """
    print("\n=== Testing Invalid Parameter Handling ===")
    try:
        sht.temperature_precision = 99
        print("ERROR: Should have raised ValueError")
    except ValueError as exc:
        print("ValueError caught (precision): %s" % exc)
    try:
        sht.heater_power = 99
        print("ERROR: Should have raised ValueError")
    except ValueError as exc:
        print("ValueError caught (heater_power): %s" % exc)
    try:
        sht.heat_time = 99
        print("ERROR: Should have raised ValueError")
    except ValueError as exc:
        print("ValueError caught (heat_time): %s" % exc)
    print("Invalid parameter tests passed")


# ======================================== 自定义类 ============================================

# ======================================== 功能函数 ============================================

# Startup

time.sleep(3)

print("FreakStudio: SHT45 Temperature and Humidity Sensor Test")
print("Author: %s" % sht45.__author__)
print("Version: %s" % sht45.__version__)

init_msg = "\nInitializing I2C (SCL=Pin(%d), SDA=Pin(%d))..."
print(init_msg % (I2C_SCL_PIN, I2C_SDA_PIN))
i2c = I2C(
    0,
    scl=Pin(I2C_SCL_PIN),
    sda=Pin(I2C_SDA_PIN),
    freq=I2C_FREQ,
)

print("Scanning I2C bus...")
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
device_list = [hex(device) for device in devices]
print("Found %d device(s): %s" % (len(devices), device_list))

sht_addr = SHT45.DEFAULT_ADDR
if sht_addr not in devices:
    error_msg = "Device not found at expected address 0x%02X"
    raise RuntimeError(error_msg % sht_addr)
print("SHT45 found at address 0x%02X" % sht_addr)

sht = SHT45(i2c, address=sht_addr)
print("SHT45 instance created")

try:
    temp, hum = sht.measurements
    initial_msg = "Initial reading: Temperature: %.2f C, Humidity: %.2f %%RH"
    print(initial_msg % (temp, hum))
    print("Sensor communication verified")
except Exception as exc:
    raise RuntimeError("Sensor verification failed: %s" % exc) from exc

print("\nInitial Configuration:")
print("  Temperature Precision: %s" % sht.temperature_precision)
print("  Heater Power: %s" % sht.heater_power)
print("  Heat Time: %s" % sht.heat_time)

print("\n--- Starting periodic measurements ---")
interval_msg = "(Interval: %d ms, I2C addr: 0x%02X)"
print(interval_msg % (_PRINT_INTERVAL_MS, sht_addr))
print("Available REPL commands:")
print("  test_all_precision_modes(sht)")
print("  test_all_heater_settings(sht)")
print("  test_invalid_params(sht)")
print("  sht.reset()")


# ========================================  主程序  ===========================================

try:
    while True:
        current_time = time.ticks_ms()
        elapsed_ms = time.ticks_diff(current_time, _last_print_time)
        if elapsed_ms >= _PRINT_INTERVAL_MS:
            temp, hum = sht.measurements
            print("[%d] Temperature: %.2f C, Humidity: %.2f %%RH" % (current_time // 1000, temp, hum))
            _last_print_time = current_time
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("\nProgram interrupted by user")
except OSError as exc:
    print("Hardware communication error: %s" % exc)
except Exception as exc:
    print("Unknown error: %s" % exc)
finally:
    print("Cleaning up resources...")
    if hasattr(sht, "deinit"):
        sht.deinit()
    del sht
    print("Program exited")
