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
import time
from lsm6dsox import LSM6DSOX, acceleration_factor, acceleration_range_values, gyro_factor, gyro_range_values, RATE_104_HZ, RANGE_4G, RANGE_250_DPS

# ======================================== globals =============================================

# ======================================== functions ===========================================

# ======================================== classes =============================================

class LSM6DSOXAsync(LSM6DSOX):
    """Call initialize_async() before use; construction performs no bus I/O."""

    def __init__(self, i2c, address=0x6A, debug=False):
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance")
        if not isinstance(address, int) or not 0 <= address <= 127:
            raise ValueError("address must be an I2C address from 0x00 to 0x7F")
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")
        self._i2c, self._address, self._debug = i2c, address, debug
        self._cached_acceleration_range = self._cached_gyro_range = 0
        self._cached_conversion_factor = self._gyro_cached_conversion_factor = 0.0
        self._initialized = False
        self._async_lock = asyncio.Lock()

    async def reset_async(self, timeout_ms=1000):
        async with self._async_lock:
            await self._reset_locked(timeout_ms)

    async def _reset_locked(self, timeout_ms):
        if not isinstance(timeout_ms, int) or timeout_ms <= 0:
            raise ValueError("timeout_ms must be a positive integer")
        self._initialized = False
        self._sw_reset = True
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while self._sw_reset:
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                raise TimeoutError("LSM6DSOX reset timeout")
            await asyncio.sleep_ms(1)

    async def initialize_async(self, timeout_ms=1500):
        """Preserve source identity/reset/configuration order within one deadline."""
        if not isinstance(timeout_ms, int) or timeout_ms <= 400:
            raise ValueError("timeout_ms must cover reset and 400 ms settling")
        async with self._async_lock:
            if self._initialized:
                return self
            deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
            identified = False
            try:
                if self._device_id != 0x6C:
                    raise RuntimeError("Failed to find LSM6DSOX: chip ID mismatch")
                identified = True
                remaining = time.ticks_diff(deadline, time.ticks_ms()) - 400
                if remaining <= 0:
                    raise TimeoutError("LSM6DSOX initialization timeout")
                await self._reset_locked(remaining)
                self._bdu = True
                self._acceleration_full_scale = False
                self._acceleration_data_rate = RATE_104_HZ
                self._gyro_data_rate = RATE_104_HZ
                await self._set_acceleration_range_locked(RANGE_4G)
                await self._set_gyro_range_locked(RANGE_250_DPS)
                if time.ticks_diff(deadline, time.ticks_ms()) < 0:
                    raise TimeoutError("LSM6DSOX initialization timeout")
                self._initialized = True
            except BaseException as error:
                self._initialized = False
                if identified:
                    try:
                        LSM6DSOX.deinit(self)
                    except BaseException as cleanup_error:
                        raise error from cleanup_error
                raise
            return self

    @classmethod
    async def create_async(cls, i2c, address=0x6A, debug=False, timeout_ms=1500):
        sensor = cls(i2c, address=address, debug=debug)
        return await sensor.initialize_async(timeout_ms)
    def _ready(self):
        if not self._initialized:
            raise RuntimeError("call initialize_async() before use")

    async def read_acceleration_async(self):
        async with self._async_lock:
            self._ready()
            return self.acceleration

    async def read_gyro_async(self):
        async with self._async_lock:
            self._ready()
            return self.gyro

    async def read_temperature_async(self):
        async with self._async_lock:
            self._ready()
            return self.temperature

    async def set_acceleration_range_async(self, value):
        async with self._async_lock:
            self._ready()
            await self._set_acceleration_range_locked(value)

    async def _set_acceleration_range_locked(self, value):
        if value not in acceleration_range_values:
            raise ValueError("Value must be a valid acceleration_range setting")
        self._acceleration_range = value
        self._cached_acceleration_range = value
        self._cached_conversion_factor = acceleration_factor[value]
        await asyncio.sleep_ms(200)

    async def set_gyro_range_async(self, value):
        async with self._async_lock:
            self._ready()
            await self._set_gyro_range_locked(value)

    async def _set_gyro_range_locked(self, value):
        if value not in gyro_range_values:
            raise ValueError("Value must be a valid gyro_range setting")
        self._cached_gyro_range = value
        self._gyro_cached_conversion_factor = gyro_factor[value]
        self._gyro_range = value
        await asyncio.sleep_ms(200)

    async def set_high_pass_filter_async(self, value):
        async with self._async_lock:
            self._ready()
            self.high_pass_filter = value

    async def aclose(self):
        async with self._async_lock:
            if self._initialized:
                self.deinit()
                self._initialized = False

# ======================================== init ================================================

# ======================================== main ================================================
