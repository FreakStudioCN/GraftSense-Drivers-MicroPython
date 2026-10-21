
# Preserve the documented exception contract on MicroPython.
try:
    TimeoutError
except NameError:
    try:
        from uasyncio import TimeoutError
    except ImportError:
        from asyncio import TimeoutError

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

    def __init__(self, address: int, i2c):
        """
        初始化 BH1750 传感器。

        Args:
            address (int): I2C 地址。
            i2c (I2C): machine.I2C 实例。

        Raises:
            TypeError: 当 address 不是 int 或 i2c 不是 I2C 实例时。
            ValueError: 当 address 不是 0x23 或 0x5C时。

        Notes:
            初始化时会写入默认测量时间和测量模式。

        ==========================================

        Initialize BH1750 sensor.

        Args:
            address (int): I2C address.
            i2c (I2C): machine.I2C instance.

        Raises:
            TypeError: If address is not int or i2c is not an I2C instance.
            ValueError: If address is not 0x23 or 0x5C.

        Notes:
            Writes default measurement time and mode during initialization.
        """
        if not isinstance(address, int):
            raise TypeError("address must be an integer")
        if not (address == 0x23 or address == 0x5C):
            raise ValueError("address must be 0x23 or 0x5C")
            # 避免直接导入 machine.I2C（兼容性），用 duck typing 检查
        if not hasattr(i2c, "writeto") or not hasattr(i2c, "readfrom_into"):
            raise TypeError("i2c must be a machine.I2C instance")
        self._address = address
        self._i2c = i2c
        self._measurement_mode = BH1750.MEASUREMENT_MODE_ONE_TIME
        self._resolution = BH1750.RESOLUTION_HIGH
        self._measurement_time = BH1750.MEASUREMENT_TIME_DEFAULT

        self._initialized = False

    async def initialize_async(self):
        if not self._initialized:
            await self.configure_async(self._measurement_mode, self._resolution, self._measurement_time)

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
        self._initialized = True

    async def reset_async(self):
        return self.reset()

    async def power_on_async(self):
        return self.power_on()

    async def power_off_async(self):
        return self.power_off()

    async def measurement_async(self, timeout_ms=250):
        await self.initialize_async()
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

    def measurements_async(self, timeout_ms=250):
        """Return an explicit async iterator supported by MicroPython 1.23."""
        return _MeasurementsAsync(self, timeout_ms)

    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit is not None:
            deinit()


class _MeasurementsAsync:
    def __init__(self, sensor, timeout_ms):
        self._sensor = sensor
        self._timeout_ms = timeout_ms
        self._first = True

    def __aiter__(self):
        return self

    async def __anext__(self):
        sensor = self._sensor
        if not self._first and sensor._measurement_mode == BH1750.MEASUREMENT_MODE_CONTINUOUSLY:
            base = 16 if sensor._measurement_time == BH1750.RESOLUTION_LOW else 120
            wait_ms = math.ceil(base * sensor._measurement_time / BH1750.MEASUREMENT_TIME_DEFAULT)
            if wait_ms > self._timeout_ms:
                raise TimeoutError("BH1750 continuous conversion timeout")
            await asyncio.sleep_ms(wait_ms)
        value = await sensor.measurement_async(self._timeout_ms)
        self._first = False
        return value
# ======================================== 初始化配置 ==========================================
# ======================================== 主程序 ==============================================
