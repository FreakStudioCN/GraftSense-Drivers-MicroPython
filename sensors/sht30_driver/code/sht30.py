# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24 00:00
# @Author  : Roberto Sanchez
# @File    : sht30.py
# @Description : SHT30 temperature and humidity sensor I2C driver
# @License : MIT
# Original license: Apache License 2.0
# Original source: Claude Skill normalized Project1 driver

__version__ = "0.2.1"
__author__ = "Roberto Sanchez"
__license__ = "Apache License 2.0"
__platform__ = "MicroPython v1.23 / RP2040"

# ======================================== 导入相关模块 =========================================

import time

import micropython
from machine import I2C

# ======================================== 全局变量 ============================================

_BUF6 = bytearray(6)
_BUF3 = bytearray(3)

# ======================================== 功能函数 ============================================


def _calc_crc(data: bytearray) -> int:
    """
    Calculate 8-bit CRC for SHT3x sensor data.
    """
    crc = 0xFF
    for value in data:
        crc ^= value
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x31
            else:
                crc <<= 1
    return crc & 0xFF


# ======================================== 自定义类 ============================================


class SHT30Error(Exception):
    """
    SHT30 sensor exception class.
    """

    BUS_ERROR = micropython.const(0x01)
    DATA_ERROR = micropython.const(0x02)
    CRC_ERROR = micropython.const(0x03)

    def __init__(self, error_code: int = None) -> None:
        if error_code is not None:
            if isinstance(error_code, int) is False:
                raise ValueError("error_code must be int")
        self.error_code = error_code
        super().__init__(self.get_message())

    def get_message(self) -> str:
        """
        Return the message matching the stored error code.
        """
        if self.error_code == SHT30Error.BUS_ERROR:
            return "Bus error"
        if self.error_code == SHT30Error.DATA_ERROR:
            return "Data error"
        if self.error_code == SHT30Error.CRC_ERROR:
            return "CRC error"
        return "Unknown error"


class SHT30:
    """
    SHT30 temperature and humidity sensor I2C driver.
    """

    DEFAULT_I2C_ADDR = micropython.const(0x45)

    POLYNOMIAL = micropython.const(0x131)

    ALERT_PENDING_MASK = micropython.const(0x8000)
    HEATER_MASK = micropython.const(0x2000)
    RH_ALERT_MASK = micropython.const(0x0800)
    T_ALERT_MASK = micropython.const(0x0400)
    RESET_MASK = micropython.const(0x0010)
    CMD_STATUS_MASK = micropython.const(0x0002)
    WRITE_STATUS_MASK = micropython.const(0x0001)

    MEASURE_CMD = b"\x2C\x10"
    STATUS_CMD = b"\xF3\x2D"
    RESET_CMD = b"\x30\xA2"
    CLEAR_STATUS_CMD = b"\x30\x41"
    ENABLE_HEATER_CMD = b"\x30\x6D"
    DISABLE_HEATER_CMD = b"\x30\x66"

    MEASURE_RESPONSE_SIZE = micropython.const(6)
    STATUS_RESPONSE_SIZE = micropython.const(3)
    MEASURE_READ_DELAY_MS = micropython.const(100)
    STATUS_READ_DELAY_MS = micropython.const(20)
    DEFAULT_RETRIES = micropython.const(2)
    DEFAULT_RETRY_DELAY_MS = micropython.const(5)
    CRC_CHUNK_SIZE = micropython.const(3)

    def __init__(self, i2c: I2C, addr: int = DEFAULT_I2C_ADDR, delta_temp: float = 0.0, delta_hum: float = 0.0, debug: bool = False) -> None:
        """
        Initialize the SHT30 sensor driver.
        """
        if hasattr(i2c, "writeto") is False or hasattr(i2c, "readfrom_into") is False:
            raise ValueError("i2c must provide writeto and readfrom_into")
        if isinstance(addr, int) is False:
            raise ValueError("addr must be int")
        if addr < 0x08 or addr > 0x77:
            raise ValueError("addr must be a valid 7-bit I2C address")
        if isinstance(delta_temp, (int, float)) is False:
            raise ValueError("delta_temp must be int or float")
        if isinstance(delta_hum, (int, float)) is False:
            raise ValueError("delta_hum must be int or float")
        if isinstance(debug, bool) is False:
            raise ValueError("debug must be bool")

        self._i2c = i2c
        self._addr = addr
        self._delta_temp = float(delta_temp)
        self._delta_hum = float(delta_hum)
        self._debug = debug

        time.sleep_ms(50)

    def is_present(self) -> bool:
        """
        Return True when the sensor address is found on the I2C bus.
        """
        return self._addr in self._i2c.scan()

    def set_delta(self, delta_temp: float = 0.0, delta_hum: float = 0.0) -> None:
        """
        Set temperature and humidity measurement offsets.
        """
        if isinstance(delta_temp, (int, float)) is False:
            raise ValueError("delta_temp must be int or float")
        if isinstance(delta_hum, (int, float)) is False:
            raise ValueError("delta_hum must be int or float")
        self._delta_temp = float(delta_temp)
        self._delta_hum = float(delta_hum)

    def measure(self, raw: bool = False) -> tuple:
        """
        Read temperature and humidity as floating point values.
        """
        if isinstance(raw, bool) is False:
            raise ValueError("raw must be bool")
        data = self._send_cmd(SHT30.MEASURE_CMD, SHT30.MEASURE_RESPONSE_SIZE, SHT30.MEASURE_READ_DELAY_MS)
        if raw:
            return data
        t_celsius = (((data[0] << 8 | data[1]) * 175) / 0xFFFF) - 45 + self._delta_temp
        rh = (((data[3] << 8 | data[4]) * 100.0) / 0xFFFF) + self._delta_hum
        return t_celsius, rh

    def measure_int(self, raw: bool = False) -> tuple:
        """
        Read temperature and humidity using integer arithmetic.
        """
        if isinstance(raw, bool) is False:
            raise ValueError("raw must be bool")
        data = self._send_cmd(SHT30.MEASURE_CMD, SHT30.MEASURE_RESPONSE_SIZE, SHT30.MEASURE_READ_DELAY_MS)
        if raw:
            return data
        aux = (data[0] << 8 | data[1]) * 175
        t_int = (aux // 0xFFFF) - 45
        t_dec = (aux % 0xFFFF * 100) // 0xFFFF
        aux = (data[3] << 8 | data[4]) * 100
        h_int = aux // 0xFFFF
        h_dec = (aux % 0xFFFF * 100) // 0xFFFF
        return t_int, t_dec, h_int, h_dec

    def status(self, raw: bool = False) -> int:
        """
        Read the sensor status register.
        """
        if isinstance(raw, bool) is False:
            raise ValueError("raw must be bool")
        data = self._send_cmd(SHT30.STATUS_CMD, SHT30.STATUS_RESPONSE_SIZE, SHT30.STATUS_READ_DELAY_MS)
        if raw:
            return data
        return data[0] << 8 | data[1]

    def clear_status(self) -> None:
        """
        Clear the sensor status register.
        """
        self._send_cmd(SHT30.CLEAR_STATUS_CMD, response_size=0)

    def reset(self) -> None:
        """
        Soft-reset the sensor.
        """
        self._send_cmd(SHT30.RESET_CMD, response_size=0)
        time.sleep_ms(20)

    def deinit(self) -> None:
        """
        Release sensor resources held by this driver instance.
        """
        self._delta_temp = 0.0
        self._delta_hum = 0.0
        self._i2c = None

    def _check_crc(self, data: bytearray) -> bool:
        """
        Return True when the CRC byte matches the two data bytes.
        """
        if isinstance(data, (bytes, bytearray, memoryview)) is False:
            raise ValueError("data must be bytes-like")
        if len(data) != SHT30.CRC_CHUNK_SIZE:
            raise ValueError("data must contain two data bytes and one CRC byte")
        crc_calc = _calc_crc(data[:2])
        return crc_calc == data[2]

    def _send_cmd(self, cmd_request: bytes, response_size: int = 0, read_delay_ms: int = 100) -> bytearray:
        """
        Send a command to the sensor and read an optional response.
        """
        if isinstance(cmd_request, (bytes, bytearray)) is False:
            raise ValueError("cmd_request must be bytes-like")
        if isinstance(response_size, int) is False:
            raise ValueError("response_size must be int")
        if response_size < 0 or response_size > SHT30.MEASURE_RESPONSE_SIZE:
            raise ValueError("response_size is out of range")
        if isinstance(read_delay_ms, int) is False:
            raise ValueError("read_delay_ms must be int")
        if read_delay_ms < 0:
            raise ValueError("read_delay_ms must be greater than or equal to 0")

        buf = _BUF6 if response_size > SHT30.STATUS_RESPONSE_SIZE else _BUF3

        for attempt in range(SHT30.DEFAULT_RETRIES + 1):
            try:
                self._i2c.writeto(self._addr, cmd_request)
                if response_size == 0:
                    return bytearray()
                time.sleep_ms(read_delay_ms)
                self._i2c.readfrom_into(self._addr, buf)
                data = buf[:response_size]

                for index in range(response_size // SHT30.CRC_CHUNK_SIZE):
                    start = index * SHT30.CRC_CHUNK_SIZE
                    chunk = data[start : start + SHT30.CRC_CHUNK_SIZE]
                    if self._check_crc(chunk) is False:
                        raise RuntimeError("CRC check failed")
                return data
            except OSError:
                if attempt == SHT30.DEFAULT_RETRIES:
                    raise RuntimeError("I2C communication failed after retries")
                self._log("I2C retry %d/%d" % (attempt + 1, SHT30.DEFAULT_RETRIES))
                time.sleep_ms(SHT30.DEFAULT_RETRY_DELAY_MS)
        raise RuntimeError("I2C communication failed")

    def _log(self, msg: str) -> None:
        """
        Print a debug message when debug output is enabled.
        """
        if isinstance(msg, str) is False:
            raise ValueError("msg must be str")
        if self._debug:
            print("[SHT30] %s" % msg)


# ======================================== 初始化配置 ===========================================

# ========================================  主程序 ============================================
