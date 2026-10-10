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

from max30102 import MAX30102


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

    async def setup_sensor_async(self, led_mode=2, adc_range=16384, sample_rate=400,
                                 led_power=MAX30105_PULSE_AMP_MEDIUM,
                                 sample_avg=8, pulse_width=411):
        async with self._async_lock:
            return self.setup_sensor(led_mode, adc_range, sample_rate, led_power,
                                     sample_avg, pulse_width)

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
            return self.read_temperature()

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
