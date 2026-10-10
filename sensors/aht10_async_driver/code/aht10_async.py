# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Andreas Bühl
# @File    : aht10_async.py
# @Description : Source-faithful asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
import aht10


# ======================================== 全局变量 ============================================
_ASYNC_FACADE_P0 = True

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================

class AHT10Async(aht10.AHT10):
    """AHT10 with explicit cooperative initialization and measurement steps."""

    def __init__(self, i2c, address=aht10.AHT10.AHT10_I2CADDR_DEFAULT, debug=False):
        if not hasattr(i2c, "writeto"):
            raise ValueError("i2c must provide writeto")
        if not isinstance(address, int) or not 0 <= address <= 0x7F:
            raise ValueError("address must be an I2C address from 0x00 to 0x7F")
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")
        self._i2c = i2c
        self._address = address
        self._debug = debug
        self._initialized = False

    async def _wait_for_idle_async(self, timeout_ms=100, poll_ms=5):
        started = time.ticks_ms()
        while self.status & self.AHT10_STATUS_BUSY:
            if time.ticks_diff(time.ticks_ms(), started) >= timeout_ms:
                raise TimeoutError("AHT10 busy flag timeout")
            await asyncio.sleep_ms(poll_ms)

    async def initialize_async(self, timeout_ms=100):
        """Perform the source constructor reset/initialize sequence cooperatively."""
        await asyncio.sleep_ms(20)
        aht10._BUF6[0] = self.AHT10_CMD_SOFTRESET
        try:
            self._i2c.writeto(self._address, aht10._BUF6[0:1])
        except OSError as error:
            raise RuntimeError("I2C write failed during reset") from error
        await asyncio.sleep_ms(20)
        aht10._BUF6[0] = self.AHT10_CMD_INITIALIZE
        aht10._BUF6[1] = 0x08
        aht10._BUF6[2] = 0x00
        try:
            self._i2c.writeto(self._address, aht10._BUF6[0:3])
        except OSError as error:
            raise RuntimeError("I2C write failed during initialize") from error
        await self._wait_for_idle_async(timeout_ms=timeout_ms)
        if not (self.status & self.AHT10_STATUS_CALIBRATED):
            raise RuntimeError("Could not initialize AHT10")
        self._initialized = True
        return True

    async def measure_async(self, timeout_ms=100):
        """Retain the source trigger, busy-status and six-byte parsing sequence."""
        if not self._initialized:
            raise RuntimeError("Call initialize_async() before measurement")
        self._trigger_measurement()
        await self._wait_for_idle_async(timeout_ms=timeout_ms)
        self._read_to_buffer()
        raw_humidity = (aht10._BUF6[1] << 12) | (aht10._BUF6[2] << 4) | (aht10._BUF6[3] >> 4)
        raw_temperature = ((aht10._BUF6[3] & 0x0F) << 16) | (aht10._BUF6[4] << 8) | aht10._BUF6[5]
        humidity = (raw_humidity * 100.0) / 0x100000
        temperature = ((raw_temperature * 200.0) / 0x100000) - 50
        return temperature, humidity

    async def aclose(self):
        self.deinit()
# ======================================== 初始化配置 ==========================================
# ======================================== 主程序 ==============================================
