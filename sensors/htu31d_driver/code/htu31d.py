# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/25
# @Author  : Jose D. Montoya
# @File    : htu31d.py
# @Description : HTU31D temperature and humidity sensor I2C driver
# @License : MIT

__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== Imports =========================================

import struct
import time

# ======================================== Global variables =========================================

_BUF4 = bytearray(4)
_BUF6 = bytearray(6)

# ======================================== Functions =========================================


def _crc8(value: int) -> int:
    """Return the HTU31D CRC-8 value for a 16-bit unsigned value."""
    if not isinstance(value, int) or not 0 <= value <= 0xFFFF:
        raise ValueError("value must be an unsigned 16-bit integer")

    crc = 0
    for shift in (8, 0):
        crc ^= value >> shift
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x31
            else:
                crc <<= 1
            crc &= 0xFF
    return crc


# ======================================== Custom classes =========================================


class HTU31D:
    """HTU31D temperature and humidity sensor driver."""

    _CMD_READ_SERIAL = 0x0A
    _CMD_SOFT_RESET = 0x1E
    _CMD_HEATER_ON = 0x04
    _CMD_HEATER_OFF = 0x02
    _CMD_CONVERSION = 0x40
    _CMD_READ_TEMP_HUM = 0x00
    I2C_DEFAULT_ADDR = 0x40

    _HUMIDITY_RES = ("0.020%", "0.014%", "0.010%", "0.007%")
    _TEMP_RES = ("0.040", "0.025", "0.016", "0.012")
    __slots__ = ("_i2c", "_addr", "_conversion_cmd", "_heater", "_debug")

    def __init__(self, i2c, address: int = I2C_DEFAULT_ADDR, debug: bool = False) -> None:
        if hasattr(i2c, "readfrom_into") is False:
            raise ValueError("i2c must provide readfrom_into")
        if hasattr(i2c, "writeto") is False:
            raise ValueError("i2c must provide writeto")
        if not isinstance(address, int) or not 0 <= address <= 0x7F:
            raise ValueError("address must be an I2C address from 0x00 to 0x7F")
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")

        self._i2c = i2c
        self._addr = address
        self._conversion_cmd = self._CMD_CONVERSION
        self._heater = False
        self._debug = debug
        self.reset()

    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        self.deinit()

    def reset(self) -> None:
        """Soft-reset the sensor and restore default conversion settings."""
        self._conversion_cmd = self._CMD_CONVERSION
        self._send_cmd(self._CMD_SOFT_RESET)
        time.sleep_ms(5)

    def deinit(self) -> None:
        """Turn off the heater when possible and release the I2C reference."""
        if self._i2c is None:
            return
        if self._heater:
            try:
                self._send_cmd(self._CMD_HEATER_OFF)
            except RuntimeError:
                pass
        self._heater = False
        self._i2c = None

    @property
    def serial_number(self) -> tuple:
        """Return the sensor serial-number response as a one-element tuple."""
        self._send_cmd(self._CMD_READ_SERIAL)
        self._read_into(_BUF4)
        serial_number = struct.unpack(">I", _BUF4)
        return serial_number

    @property
    def heater(self) -> bool:
        """Return the cached heater state."""
        return self._heater

    @heater.setter
    def heater(self, new_mode: bool) -> None:
        if isinstance(new_mode, bool) is False:
            raise ValueError("heater mode must be bool")
        self._send_cmd(self._CMD_HEATER_ON if new_mode else self._CMD_HEATER_OFF)
        self._heater = new_mode

    @property
    def relative_humidity(self) -> float:
        """Return a new relative-humidity measurement in %RH."""
        return self.measurements[1]

    @property
    def temperature(self) -> float:
        """Return a new temperature measurement in degrees Celsius."""
        return self.measurements[0]

    @property
    def measurements(self) -> tuple:
        """Return a new ``(temperature, relative_humidity)`` measurement tuple."""
        self._send_cmd(self._conversion_cmd)
        time.sleep_ms(30)
        self._send_cmd(self._CMD_READ_TEMP_HUM)
        self._read_into(_BUF6)
        temperature, temp_crc, humidity, humidity_crc = struct.unpack_from(">HBHB", _BUF6)

        if temp_crc != _crc8(temperature) or humidity_crc != _crc8(humidity):
            raise RuntimeError("CRC check failed on sensor data")

        temperature = -40.0 + 165.0 * temperature / 65535.0
        humidity = 100.0 * humidity / 65535.0
        humidity = max(0.0, min(humidity, 100.0))
        return temperature, humidity

    @property
    def humidity_resolution(self) -> str:
        """Return the selected humidity resolution."""
        return self._HUMIDITY_RES[(self._conversion_cmd >> 3) & 3]

    @humidity_resolution.setter
    def humidity_resolution(self, value: str) -> None:
        if value not in self._HUMIDITY_RES:
            raise ValueError("humidity resolution must be a supported resolution")
        self._conversion_cmd = (self._conversion_cmd & 0xE7) | (self._HUMIDITY_RES.index(value) << 3)

    @property
    def temp_resolution(self) -> str:
        """Return the selected temperature resolution."""
        return self._TEMP_RES[(self._conversion_cmd >> 1) & 3]

    @temp_resolution.setter
    def temp_resolution(self, value: str) -> None:
        if value not in self._TEMP_RES:
            raise ValueError("temperature resolution must be a supported resolution")
        self._conversion_cmd = (self._conversion_cmd & 0xF9) | (self._TEMP_RES.index(value) << 1)

    def _send_cmd(self, cmd: int) -> None:
        if not isinstance(cmd, int) or not 0 <= cmd <= 0xFF:
            raise ValueError("cmd must be an unsigned byte")
        if self._i2c is None:
            raise RuntimeError("sensor has been deinitialized")
        try:
            self._i2c.writeto(self._addr, bytes((cmd,)), False)
        except OSError:
            raise RuntimeError("I2C command write failed")

    def _read_into(self, buf: bytearray) -> None:
        if not isinstance(buf, bytearray):
            raise ValueError("buf must be bytearray")
        if self._i2c is None:
            raise RuntimeError("sensor has been deinitialized")
        try:
            self._i2c.readfrom_into(self._addr, buf)
        except OSError:
            raise RuntimeError("I2C read failed")

    def _log(self, msg: str) -> None:
        if isinstance(msg, str) is False:
            raise ValueError("msg must be str")
        if self._debug:
            print("[HTU31D] %s" % msg)


# ======================================== Initialization configuration =========================================

# ======================================== Main program ===========================================
