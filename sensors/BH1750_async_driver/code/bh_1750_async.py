# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : 缪贵成
# @File    : bh_1750_async.py
# @Description : Asynchronous driver facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import math
from bh_1750 import *

# ======================================== 全局变量 ============================================
_ASYNC_FACADE_P0 = True

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 =============================================


class BH1750Async(BH1750):
    """BH1750 cooperative conversion API; I2C transactions remain short and synchronous."""

    def _conversion_ms(self):
        if self._measurement_time == BH1750.RESOLUTION_LOW:
            return 24
        return 180

    async def configure_async(self, measurement_mode, resolution, measurement_time):
        self._measurement_mode = measurement_mode
        self._resolution = resolution
        self._measurement_time = measurement_time
        self._write_measurement_time()
        buffer = bytearray(1)
        buffer[0] = self._measurement_mode << 4 | self._resolution
        self._i2c.writeto(self._address, buffer)
        await asyncio.sleep_ms(self._conversion_ms())

    async def reset_async(self):
        return self.reset()

    async def power_on_async(self):
        return self.power_on()

    async def power_off_async(self):
        return self.power_off()

    async def measurement_async(self, timeout_ms=250):
        if self._measurement_mode == BH1750.MEASUREMENT_MODE_ONE_TIME:
            buffer = bytearray(1)
            buffer[0] = self._measurement_mode << 4 | self._resolution
            self._i2c.writeto(self._address, buffer)
            wait_ms = self._conversion_ms()
            if wait_ms > timeout_ms:
                raise TimeoutError("BH1750 conversion timeout")
            await asyncio.sleep_ms(wait_ms)
        buffer = bytearray(2)
        self._i2c.readfrom_into(self._address, buffer)
        lux = (buffer[0] << 8 | buffer[1]) / (1.2 * (BH1750.MEASUREMENT_TIME_DEFAULT / self._measurement_time))
        if self._resolution == BH1750.RESOLUTION_HIGH_2:
            return lux / 2
        return lux

    async def measurements_async(self, timeout_ms=250):
        while True:
            yield await self.measurement_async(timeout_ms)
            if self._measurement_mode == BH1750.MEASUREMENT_MODE_CONTINUOUSLY:
                base = 16 if self._measurement_time == BH1750.RESOLUTION_LOW else 120
                wait_ms = math.ceil(base * self._measurement_time / BH1750.MEASUREMENT_TIME_DEFAULT)
                if wait_ms > timeout_ms:
                    raise TimeoutError("BH1750 continuous conversion timeout")
                await asyncio.sleep_ms(wait_ms)

    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit is not None:
            deinit()
# ======================================== 初始化配置 ==========================================
# ======================================== 主程序 ==============================================
