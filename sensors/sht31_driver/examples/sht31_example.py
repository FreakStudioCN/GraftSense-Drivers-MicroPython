# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/31 12:00
# @Author  : Kai Fricke
# @File    : sht31Example.py
# @Description : Minimal SHT31 usage example
# @License : MIT

__version__ = "1.0.0"
__author__ = "Kai Fricke"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

from machine import I2C, Pin
import sht31


def run_example() -> tuple:
    """Read and return one SHT31 temperature and humidity sample."""
    i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
    sensor = sht31.SHT31(i2c, addr=0x44)
    try:
        return sensor.get_temp_humi()
    finally:
        sensor.deinit()


if __name__ == "__main__":
    temperature, humidity = run_example()
    print("T=%.2f C  RH=%.2f %%" % (temperature, humidity))
