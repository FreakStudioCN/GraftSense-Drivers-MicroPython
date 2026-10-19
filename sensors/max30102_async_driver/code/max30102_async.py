# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : GraftSense Async Conversion
# @File    : max30102_async.py
# @Description : Asynchronous runtime helper
# @License : MIT

# ======================================== imports =============================================

"""Serialized async facade for bounded MAX30102 I2C transactions."""

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time

from _gs_max30102_max30102 import MAX30102, MAX30105_PULSE_AMP_MEDIUM, MAX30105_MODE_CONFIG, MAX30105_RESET_MASK, MAX30105_RESET, MAX30105_DIE_TEMP_CONFIG, MAX30105_INT_STAT_2, MAX30105_INT_DIE_TEMP_RDY_ENABLE, MAX30105_DIE_TEMP_INT, MAX30105_DIE_TEMP_FRAC


# ======================================== globals =============================================

# ======================================== functions ===========================================

# ======================================== classes =============================================

class MAX30102Async(MAX30102):
    """Explicit adapters; individual I2C accesses remain synchronous."""

    def __init__(self, i2c):
        self._async_lock = asyncio.Lock()
        super().__init__(i2c=i2c)

    async def check_part_id_async(self):
        async with self._async_lock:
            return self.check_part_id()

    async def _soft_reset_async(self, timeout_ms=1000):
        self.set_bitmask(MAX30105_MODE_CONFIG, MAX30105_RESET_MASK, MAX30105_RESET)
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while True:
            await asyncio.sleep_ms(10)
            status = ord(self.i2c_read_register(MAX30105_MODE_CONFIG))
            if (status & MAX30105_RESET) == 0:
                return
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                raise RuntimeError("MAX30102 reset timeout")

    async def setup_sensor_async(self, led_mode=2, adc_range=16384, sample_rate=400,
                                 led_power=MAX30105_PULSE_AMP_MEDIUM,
                                 sample_avg=8, pulse_width=411):
        async with self._async_lock:
            await self._soft_reset_async()
            self.set_fifo_average(sample_avg)
            self.enable_fifo_rollover()
            self.set_led_mode(led_mode)
            self.set_adc_range(adc_range)
            self.set_sample_rate(sample_rate)
            self.set_pulse_width(pulse_width)
            self.set_pulse_amplitude_red(led_power)
            self.set_pulse_amplitude_it(led_power)
            self.set_pulse_amplitude_green(led_power)
            self.set_pulse_amplitude_proximity(led_power)
            return self.clear_fifo()

    async def set_sample_rate_async(self, value):
        async with self._async_lock:
            return self.set_sample_rate(value)

    async def set_fifo_average_async(self, value):
        async with self._async_lock:
            return self.set_fifo_average(value)

    async def set_active_leds_amplitude_async(self, value):
        async with self._async_lock:
            return self.set_active_leds_amplitude(value)

    async def read_temperature_async(self):
        async with self._async_lock:
            self.i2c_set_register(MAX30105_DIE_TEMP_CONFIG, 0x01)
            await asyncio.sleep_ms(100)
            deadline = time.ticks_add(time.ticks_ms(), 1000)
            while ord(self.i2c_read_register(MAX30105_INT_STAT_2)) & MAX30105_INT_DIE_TEMP_RDY_ENABLE:
                if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                    raise RuntimeError("MAX30102 temperature timeout")
                await asyncio.sleep_ms(1)
            temp_int = ord(self.i2c_read_register(MAX30105_DIE_TEMP_INT))
            temp_frac = ord(self.i2c_read_register(MAX30105_DIE_TEMP_FRAC))
            return float(temp_int) + (float(temp_frac) * 0.0625)

    async def check_async(self):
        async with self._async_lock:
            return self.check()

    async def available_async(self):
        async with self._async_lock:
            return self.available()

    async def pop_red_from_storage_async(self):
        async with self._async_lock:
            return self.pop_red_from_storage()

    async def pop_ir_from_storage_async(self):
        async with self._async_lock:
            return self.pop_ir_from_storage()

    def deinit(self):
        shutdown = getattr(self, "shutdown", None)
        if shutdown is not None:
            shutdown()

    async def aclose(self):
        self.deinit()

# ======================================== init ================================================

# ======================================== main ================================================
