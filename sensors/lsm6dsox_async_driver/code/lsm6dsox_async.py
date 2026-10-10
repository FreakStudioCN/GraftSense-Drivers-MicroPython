# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Jose D. Montoya
# @File    : lsm6dsox_async.py
# @Description : LSM6DSOX bounded-I2C asynchronous adapter
# @License : MIT

# ======================================== imports =============================================

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from lsm6dsox import LSM6DSOX, acceleration_factor, acceleration_range_values, gyro_factor, gyro_range_values

# ======================================== globals =============================================

# ======================================== functions ===========================================

# ======================================== classes =============================================

class LSM6DSOXAsync(LSM6DSOX):
    """Explicit awaitable accessors that preserve source register/cache order."""
    async def read_acceleration_async(self): return self.acceleration
    async def read_gyro_async(self): return self.gyro
    async def read_temperature_async(self): return self.temperature

    async def set_acceleration_range_async(self, value):
        if value not in acceleration_range_values:
            raise ValueError("Value must be a valid acceleration_range setting")
        self._acceleration_range = value
        self._cached_acceleration_range = value
        self._cached_conversion_factor = acceleration_factor[value]
        await asyncio.sleep_ms(200)

    async def set_gyro_range_async(self, value):
        if value not in gyro_range_values:
            raise ValueError("Value must be a valid gyro_range setting")
        self._cached_gyro_range = value
        self._gyro_cached_conversion_factor = gyro_factor[value]
        self._gyro_range = value
        await asyncio.sleep_ms(200)

    async def set_high_pass_filter_async(self, value):
        self.high_pass_filter = value

    async def aclose(self): self.deinit()

# ======================================== init ================================================

# ======================================== main ================================================