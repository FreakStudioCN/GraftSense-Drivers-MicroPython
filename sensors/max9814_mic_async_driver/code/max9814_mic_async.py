# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : FreakStudio
# @File    : max9814_mic_async.py
# @Description : MAX9814 microphone asynchronous adapter
# @License : MIT

# ======================================== imports =============================================

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from max9814_mic import MAX9814Mic

# ======================================== globals =============================================

# ======================================== functions ===========================================

# ======================================== classes =============================================

class MAX9814MicAsync(MAX9814Mic):
    """Async facade for bounded ADC reads and cooperative multi-sample operations."""

    async def read_async(self): return self.read()
    async def read_normalized_async(self): return self.read_normalized()
    async def read_voltage_async(self, vref=3.3): return self.read_voltage(vref)
    async def set_gain_async(self, high): return self.set_gain(high)
    async def get_state_async(self): return self.get_state()

    async def get_average_reading_async(self, samples=10):
        if samples <= 0: raise ValueError("samples must > 0")
        total = 0
        for _ in range(samples):
            total += self.read()
            await asyncio.sleep_ms(0)
        return total // samples

    async def get_peak_reading_async(self, samples=100):
        if samples <= 0: raise ValueError("samples must > 0")
        peak = 0
        for _ in range(samples):
            reading = self.read()
            if reading > peak: peak = reading
            await asyncio.sleep_ms(0)
        return peak

    async def detect_sound_level_async(self, threshold=35000, samples=50):
        if samples <= 0: raise ValueError("samples must > 0")
        for _ in range(samples):
            if self.read() > threshold: return True
            await asyncio.sleep_ms(0)
        return False

    async def calibrate_baseline_async(self, samples=100):
        return await self.get_average_reading_async(samples)

    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit is not None: deinit()

# ======================================== init ================================================

# ======================================== main ================================================