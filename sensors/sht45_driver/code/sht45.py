# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24 00:00
# @Author  : Jose D. Montoya
# @File    : sht45.py
# @Description : Sensirion SHT45 temperature and humidity sensor driver
# @License : MIT

__version__ = "0.0.0+auto.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# 导入相关模块

import struct
import time

try:
    from micropython import const
except ImportError:

    def const(value):
        return value


# 全局变量

_BUF6 = bytearray(6)

_RESET = const(0x94)

HIGH_PRECISION = const(0)
MEDIUM_PRECISION = const(1)
LOW_PRECISION = const(2)
temperature_precision_options = (
    HIGH_PRECISION,
    MEDIUM_PRECISION,
    LOW_PRECISION,
)
temperature_precision_values = {
    HIGH_PRECISION: const(0xFD),
    MEDIUM_PRECISION: const(0xF6),
    LOW_PRECISION: const(0xE0),
}

HEATER200mW = const(0)
HEATER110mW = const(1)
HEATER20mW = const(2)
heater_power_values = (HEATER200mW, HEATER110mW, HEATER20mW)

TEMP_1 = const(0)
TEMP_0_1 = const(1)
heat_time_values = (TEMP_1, TEMP_0_1)

wat_config = {
    HEATER200mW: (0x39, 0x32),
    HEATER110mW: (0x2F, 0x24),
    HEATER20mW: (0x1E, 0x15),
}


# 功能函数


def _crc8(buffer) -> int:
    """
    Calculate CRC-8 checksum with polynomial 0x31 and initial value 0xFF.
    """
    crc = 0xFF
    for byte in buffer:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x31
            else:
                crc = crc << 1
    return crc & 0xFF


# 自定义类


class SHT45:
    """
    SHT45 temperature and humidity sensor driver.
    """

    DEFAULT_ADDR = const(0x44)

    def __init__(
        self,
        i2c: object,
        address: int = DEFAULT_ADDR,
        debug: bool = False,
    ):
        if not hasattr(i2c, "writeto") or not hasattr(i2c, "readfrom_into"):
            raise ValueError("i2c must provide writeto and readfrom_into")
        if not isinstance(address, int):
            raise ValueError("address must be int")
        if address < 0x08 or address > 0x77:
            raise ValueError("address must be in range 0x08 to 0x77")
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")

        self._i2c = i2c
        self._addr = address
        self._data = _BUF6
        self._debug = debug
        self._command = temperature_precision_values[HIGH_PRECISION]
        self._temperature_precision = HIGH_PRECISION
        self._heater_power = HEATER20mW
        self._heat_time = TEMP_0_1

    def reset(self):
        try:
            self._i2c.writeto(self._addr, bytes([_RESET]), False)
        except OSError as exc:
            raise RuntimeError("I2C write reset command failed") from exc
        time.sleep(0.1)

    def deinit(self):
        self._i2c = None

    @property
    def measurements(self):
        try:
            self._i2c.writeto(self._addr, bytes([self._command]), False)
        except OSError as exc:
            raise RuntimeError("I2C write measurement command failed") from exc

        if self._command in (0x39, 0x2F, 0x1E):
            time.sleep(1.2)
        elif self._command in (0x32, 0x24, 0x15):
            time.sleep(0.2)
        time.sleep(0.2)

        try:
            self._i2c.readfrom_into(self._addr, self._data)
        except OSError as exc:
            raise RuntimeError("I2C read measurement data failed") from exc

        temperature, temp_crc, humidity, humidity_crc = struct.unpack_from(">HBHB", self._data)

        if temp_crc != _crc8(self._data[0:2]):
            raise RuntimeError("temperature CRC check failed")
        if humidity_crc != _crc8(self._data[3:5]):
            raise RuntimeError("humidity CRC check failed")

        temperature = -45.0 + 175.0 * temperature / 65535.0
        humidity = -6.0 + 125.0 * humidity / 65535.0
        humidity = max(min(humidity, 100.0), 0.0)

        return temperature, humidity

    @property
    def temperature(self):
        return self.measurements[0]

    @property
    def relative_humidity(self):
        return self.measurements[1]

    @property
    def temperature_precision(self):
        values = ("HIGH_PRECISION", "MEDIUM_PRECISION", "LOW_PRECISION")
        return values[self._temperature_precision]

    @temperature_precision.setter
    def temperature_precision(self, value: int):
        if value not in temperature_precision_values:
            raise ValueError("invalid temperature_precision")
        self._temperature_precision = value
        self._command = temperature_precision_values[value]

    @property
    def heater_power(self):
        values = ("HEATER200mW", "HEATER110mW", "HEATER20mW")
        return values[self._heater_power]

    @heater_power.setter
    def heater_power(self, value: int):
        if value not in heater_power_values:
            raise ValueError("invalid heater_power")
        self._heater_power = value
        self._command = wat_config[value][self._heat_time]

    @property
    def heat_time(self):
        values = ("TEMP_1", "TEMP_0_1")
        return values[self._heat_time]

    @heat_time.setter
    def heat_time(self, value: int):
        if value not in heat_time_values:
            raise ValueError("invalid heat_time")
        self._heat_time = value
        self._command = wat_config[self._heater_power][value]


SHT4X = SHT45

# 初始化配置

# 主程序
