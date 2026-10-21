
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
# @Author  : Adafruit Industries
# @File    : dps310_async.py
# @Description : Explicit bounded-transaction DPS310 async facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
from micropython_dps310 import dps310 as source
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
import struct

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class DPS310Async(source.DPS310):
    """Construct without I/O, then await initialize_async()."""
    def __init__(self, i2c, address=0x77):
        if i2c is None:
            raise ValueError('I2C instance cannot be None')
        self._i2c, self._address = i2c, address
        self._initialized = False
        self._async_lock = asyncio.Lock()

    async def _wait_flag_async(self, name, deadline):
        while not getattr(self, name):
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                raise TimeoutError('DPS310 initialization timeout: '+name)
            await asyncio.sleep_ms(1)

    async def initialize_async(self, timeout_ms=2000):
        if not isinstance(timeout_ms, int) or timeout_ms <= 0:
            raise ValueError('timeout_ms must be positive')
        async with self._async_lock:
            if self._initialized:
                return self
            deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
            if self._device_id != 0x10:
                raise RuntimeError('Failed to find the DPS310 sensor!')
            self._pressure_scale = self._temp_scale = None
            self._oversample_scalefactor = (524288.0, 1572864.0, 3670016.0, 7864320.0,
                                           253952.0, 516096.0, 1040384.0, 2088960.0)
            self._sea_level_pressure = 1013.25
            self._correct_temp()
            await self._wait_flag_async('_coefficients_ready', deadline)
            # Source calibration decoding, separated from its unbounded wait.
            coeffs = [struct.unpack('B', self._i2c.readfrom_mem(self._address, 0x10+i, 1))[0]
                      for i in range(18)]
            self._c0 = self._twos_complement(coeffs[0] << 4 | (coeffs[1] >> 4 & 15), 12)
            self._c1 = self._twos_complement((coeffs[1] & 15) << 8 | coeffs[2], 12)
            self._c00 = self._twos_complement(coeffs[3] << 12 | coeffs[4] << 4 | (coeffs[5] >> 4 & 15), 20)
            self._c10 = self._twos_complement((coeffs[5] & 15) << 16 | coeffs[6] << 8 | coeffs[7], 20)
            self._c01 = self._twos_complement(coeffs[8] << 8 | coeffs[9], 16)
            self._c11 = self._twos_complement(coeffs[10] << 8 | coeffs[11], 16)
            self._c20 = self._twos_complement(coeffs[12] << 8 | coeffs[13], 16)
            self._c21 = self._twos_complement(coeffs[14] << 8 | coeffs[15], 16)
            self._c30 = self._twos_complement(coeffs[16] << 8 | coeffs[17], 16)
            self._temp_measurement_src_bit = self._calib_coeff_temp_src_bit
            self.pressure_oversample = source.RATE_64_HZ
            self.temperature_oversample = source.RATE_64_HZ
            self._sensor_mode = source.CONT_PRESTEMP
            await self._wait_flag_async('_temp_ready', deadline)
            await self._wait_flag_async('_pressure_ready', deadline)
            if time.ticks_diff(deadline, time.ticks_ms()) < 0:
                raise TimeoutError('DPS310 initialization timeout')
            self._initialized = True
            return self

    @classmethod
    async def create_async(cls, i2c, address=0x77, timeout_ms=2000):
        return await cls(i2c, address).initialize_async(timeout_ms)

    async def _get_async(self, name):
        async with self._async_lock:
            if not self._initialized: raise RuntimeError('Call initialize_async() before use')
            return getattr(self, name)

    async def _set_async(self, name, value):
        async with self._async_lock:
            if not self._initialized: raise RuntimeError('Call initialize_async() before use')
            setattr(self, name, value)

    async def get_pressure_async(self): return await self._get_async('pressure')
    async def get_altitude_async(self): return await self._get_async('altitude')
    async def get_temperature_async(self): return await self._get_async('temperature')
    async def get_sea_level_pressure_async(self): return await self._get_async('sea_level_pressure')
    async def set_pressure_oversample_async(self, value): await self._set_async('pressure_oversample', value)
    async def set_pressure_rate_async(self, value): await self._set_async('pressure_rate', value)
    async def set_temperature_oversample_async(self, value): await self._set_async('temperature_oversample', value)
    async def set_temperature_rate_async(self, value): await self._set_async('temperature_rate', value)
    async def set_mode_async(self, value): await self._set_async('mode', value)
    async def aclose(self):
        async with self._async_lock:
            deinit = getattr(self, "deinit", None)
            if deinit is not None: deinit()
            self._initialized = False

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ==============================================
