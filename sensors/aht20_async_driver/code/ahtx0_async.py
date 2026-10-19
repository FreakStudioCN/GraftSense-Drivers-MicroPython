# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Andreas Bühl, Kattni Rembor
# @File    : ahtx0_async.py
# @Description : Source-faithful asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
import _gs_aht20_ahtx0 as ahtx0


# ======================================== 全局变量 ============================================
_ASYNC_FACADE_P0 = True

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================

class AHT20Async(ahtx0.AHT20):
    """AHT20 with explicit cooperative initialization and measurement steps."""

    def __init__(self, i2c, address=ahtx0.AHT10.AHTX0_I2CADDR_DEFAULT, debug=False):
        if not hasattr(i2c, "writeto"):
            raise ValueError("i2c must be an I2C instance")
        if not isinstance(address, int) or not 0x00 <= address <= 0x7F:
            raise ValueError("address must be int in 0x00~0x7F, got %s" % address)
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")
        self._i2c = i2c
        self._address = address
        self._debug = debug
        self._buf = bytearray(6)
        self._temp = None
        self._humidity = None
        self._initialized = False

    async def _wait_for_idle_async(self, timeout_ms=100, poll_ms=5):
        started = time.ticks_ms()
        while self.status & self.AHTX0_STATUS_BUSY:
            if time.ticks_diff(time.ticks_ms(), started) >= timeout_ms:
                raise TimeoutError("AHT20 busy flag timeout")
            await asyncio.sleep_ms(poll_ms)

    async def initialize_async(self, timeout_ms=100):
        """Perform the source constructor reset/calibration sequence cooperatively."""
        await asyncio.sleep_ms(20)
        self._buf[0] = self.AHTX0_CMD_SOFTRESET
        try:
            self._i2c.writeto(self._address, self._buf[0:1])
        except OSError as error:
            raise RuntimeError("I2C write failed during reset") from error
        await asyncio.sleep_ms(20)
        self._buf[0] = self.AHTX0_CMD_INITIALIZE
        self._buf[1] = 0x08
        self._buf[2] = 0x00
        try:
            self._i2c.writeto(self._address, self._buf[0:3])
        except OSError as error:
            raise RuntimeError("I2C write failed during initialize") from error
        await self._wait_for_idle_async(timeout_ms=timeout_ms)
        if not (self.status & self.AHTX0_STATUS_CALIBRATED):
            raise RuntimeError("Could not initialize AHT sensor")
        self._initialized = True
        return True

    async def measure_async(self, timeout_ms=100):
        """Retain the source trigger, busy-status and temperature/humidity parsing."""
        if not self._initialized:
            raise RuntimeError("Call initialize_async() before measurement")
        self._trigger_measurement()
        await self._wait_for_idle_async(timeout_ms=timeout_ms)
        self._read_to_buffer()
        raw_humidity = (self._buf[1] << 12) | (self._buf[2] << 4) | (self._buf[3] >> 4)
        raw_temperature = ((self._buf[3] & 0x0F) << 16) | (self._buf[4] << 8) | self._buf[5]
        self._humidity = (raw_humidity * 100.0) / 0x100000
        self._temp = ((raw_temperature * 200.0) / 0x100000) - 50
        return self._temp, self._humidity

    async def aclose(self):
        self.deinit()
# ======================================== 初始化配置 ==========================================
# ======================================== 主程序 ==============================================
