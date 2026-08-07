# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23
# @Author  : Limor 'Ladyada' Fried, Jeff Raber
# @File    : test_i2c.py
# @Description : BME680 I2C interface test
# @License : MIT

__version__ = "1.0.0"
__author__ = "Limor 'Ladyada' Fried, Jeff Raber"
__license__ = "MIT"
__platform__ = "MicroPython"


# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin
from bme680 import BME680_I2C
import time


# ======================================== 全局变量 ============================================

# Raspberry Pi Pico / RP2040
# SDA -> GP4
# SCL -> GP5
# VCC -> 3V3
# GND -> GND
I2C_ID = 0
SDA_PIN = 4
SCL_PIN = 5
I2C_FREQ = 400000

BME680_DEFAULT_ADDR = 0x77
BME680_ALT_ADDR = 0x76

PRINT_INTERVAL_S = 2


# ======================================== 功能函数 ============================================


def main():
    bme = None
    i2c = None

    try:
        # 上电稳定延时
        time.sleep(1)

        # 程序启动标头
        print()
        print("FreakStudio: BME680 I2C Interface Test")
        print("=" * 60)

        # 初始化 I2C
        print("Initializing I2C bus...")

        i2c = I2C(I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=I2C_FREQ)

        print("I2C%d: SDA=GP%d, SCL=GP%d, Frequency=%d Hz" % (I2C_ID, SDA_PIN, SCL_PIN, I2C_FREQ))

        # 扫描 I2C 设备
        devices = i2c.scan()

        print("I2C bus scan result: %s" % (["0x%02x" % device for device in devices] if devices else "No devices found"))

        if not devices:
            raise RuntimeError("No I2C devices found. Check wiring and power supply.")

        # 自动判断 BME680 地址
        if BME680_DEFAULT_ADDR in devices:
            address = BME680_DEFAULT_ADDR
        elif BME680_ALT_ADDR in devices:
            address = BME680_ALT_ADDR
        else:
            raise RuntimeError("BME680 not found at 0x77 or 0x76. " "Check wiring and SDO pin.")

        print("BME680 detected at address 0x%02x" % address)
        print("Initializing BME680 sensor...")

        # 创建传感器实例
        bme = BME680_I2C(i2c, address=address)

        print("BME680 I2C initialized successfully")
        print("Temperature oversampling: %dx" % bme.temperature_oversample)
        print("Pressure oversampling:    %dx" % bme.pressure_oversample)
        print("Humidity oversampling:    %dx" % bme.humidity_oversample)
        print("IIR filter size:          %d" % bme.filter_size)

        print("=" * 60)
        print("Starting sensor readings...")
        print("Press Ctrl+C to stop the program")
        print("=" * 60)

        # 持续读取传感器
        while True:
            print("Temp: %.2f C  " "Hum: %.2f %%  " "Pressure: %.2f hPa  " "Gas: %d ohm" % (bme.temperature, bme.humidity, bme.pressure, bme.gas))

            time.sleep(PRINT_INTERVAL_S)

    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("Program interrupted by user")

    except OSError as e:
        print()
        print("=" * 60)
        print("Hardware communication error: %s" % str(e))

    except Exception as e:
        print()
        print("=" * 60)
        print("Program error: %s" % str(e))

    finally:
        print("Cleaning up resources...")

        if bme is not None:
            bme.deinit()
            del bme

        if i2c is not None:
            try:
                i2c.deinit()
            except AttributeError:
                # 某些 MicroPython 版本的 I2C 没有 deinit()
                pass

        print("Program exited")
        print("=" * 60)


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================

main()
