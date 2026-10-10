# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Jose D. Montoya
# @File    : htu31d_async.py
# @Description : HTU31D asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
"""Cooperative HTU31D measurement API."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import struct
import time
from htu31d import HTU31D, _BUF4, _BUF6, _crc8


# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class HTU31DAsync(HTU31D):
    """Preserves source commands, CRC and scaling; yields conversion waits."""

    CONVERSION_DELAY_MS = 30
    RESET_DELAY_MS = 5

    def __init__(self, i2c, address=HTU31D.I2C_DEFAULT_ADDR, debug=False):
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

    async def initialize_async(self):
        self._conversion_cmd = self._CMD_CONVERSION
        self._send_cmd(self._CMD_SOFT_RESET)
        await asyncio.sleep_ms(self.RESET_DELAY_MS)

    async def reset_async(self):
        await self.initialize_async()

    async def serial_number_async(self):
        self._send_cmd(self._CMD_READ_SERIAL)
        self._read_into(_BUF4)
        return struct.unpack(">I", _BUF4)

    async def set_heater_async(self, new_mode):
        if isinstance(new_mode, bool) is False:
            raise ValueError("heater mode must be bool")
        self._send_cmd(self._CMD_HEATER_ON if new_mode else self._CMD_HEATER_OFF)
        self._heater = new_mode

    async def measurements_async(self, timeout_ms=100):
        if not isinstance(timeout_ms, int) or timeout_ms < self.CONVERSION_DELAY_MS:
            raise ValueError("timeout_ms must be at least %d" % self.CONVERSION_DELAY_MS)
        started = time.ticks_ms()
        self._send_cmd(self._conversion_cmd)
        await asyncio.sleep_ms(self.CONVERSION_DELAY_MS)
        if time.ticks_diff(time.ticks_ms(), started) > timeout_ms:
            raise RuntimeError("HTU31D measurement timeout")
        self._send_cmd(self._CMD_READ_TEMP_HUM)
        self._read_into(_BUF6)
        temperature, temp_crc, humidity, humidity_crc = struct.unpack_from(">HBHB", _BUF6)
        if temp_crc != _crc8(temperature) or humidity_crc != _crc8(humidity):
            raise RuntimeError("CRC check failed on sensor data")
        temperature = -40.0 + 165.0 * temperature / 65535.0
        humidity = 100.0 * humidity / 65535.0
        humidity = max(0.0, min(humidity, 100.0))
        return temperature, humidity

    async def aclose(self):
        self.deinit()

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ===============================================
