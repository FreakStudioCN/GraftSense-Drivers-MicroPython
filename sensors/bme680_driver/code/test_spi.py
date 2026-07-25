# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23
# @Author  : Limor 'Ladyada' Fried, Jeff Raber
# @File    : test_spi.py
# @Description : BME680 SPI interface test
# @License : MIT

__version__ = "1.0.0"
__author__ = "Limor 'Ladyada' Fried, Jeff Raber"
__license__ = "MIT"
__platform__ = "MicroPython"

from machine import Pin, SPI
from bme680 import BME680_SPI
import time


# ======================================== 初始化配置 ==========================================

# Raspberry Pi Pico / RP2040 SPI0 接线：
# SCK      -> GP18
# MOSI/SDI -> GP19
# MISO/SDO -> GP16
# CS       -> GP17
# VCC      -> 3V3
# GND      -> GND

SPI_ID = 0
SCK_PIN = 18
MOSI_PIN = 19
MISO_PIN = 16
CS_PIN = 17

SPI_BAUDRATE = 1000000
PRINT_INTERVAL_S = 2


# ======================================== 主程序 ==============================================


def main():
    bme = None
    spi = None
    cs = None

    try:
        # 上电稳定延时
        time.sleep(1)

        # 程序启动标头
        print()
        print("FreakStudio: BME680 SPI Interface Test")
        print("=" * 60)

        print("Initializing SPI bus...")

        # 初始化 CS 引脚，默认拉高，不选中设备
        cs = Pin(CS_PIN, Pin.OUT, value=1)

        # 初始化 SPI 总线
        spi = SPI(
            SPI_ID, baudrate=SPI_BAUDRATE, polarity=0, phase=0, bits=8, firstbit=SPI.MSB, sck=Pin(SCK_PIN), mosi=Pin(MOSI_PIN), miso=Pin(MISO_PIN)
        )

        print("SPI%d: SCK=GP%d, MOSI=GP%d, MISO=GP%d, CS=GP%d" % (SPI_ID, SCK_PIN, MOSI_PIN, MISO_PIN, CS_PIN))

        print("SPI baudrate: %d Hz" % SPI_BAUDRATE)
        print("SPI mode: polarity=0, phase=0")
        print("Initializing BME680 sensor...")

        # 创建 BME680 SPI 传感器实例
        bme = BME680_SPI(spi, cs)

        print("BME680 SPI initialized successfully")
        print("Temperature oversampling: %dx" % bme.temperature_oversample)
        print("Pressure oversampling:    %dx" % bme.pressure_oversample)
        print("Humidity oversampling:    %dx" % bme.humidity_oversample)
        print("IIR filter size:          %d" % bme.filter_size)

        print("=" * 60)
        print("Starting sensor readings...")
        print("Press Ctrl+C to stop the program")
        print("=" * 60)

        # 持续读取传感器数据
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

        # BME680_SPI.deinit() 会先将 CS 拉高，
        # 然后清除驱动内部对 SPI 和 CS 的引用
        if bme is not None:
            bme.deinit()
            del bme

        # 释放 SPI 外设
        if spi is not None:
            try:
                spi.deinit()
            except AttributeError:
                # 某些 MicroPython 版本可能不提供 deinit()
                pass

        # 确保退出时 CS 保持高电平
        if cs is not None:
            try:
                cs.value(1)
            except Exception:
                pass

        print("Program exited")
        print("=" * 60)


main()
