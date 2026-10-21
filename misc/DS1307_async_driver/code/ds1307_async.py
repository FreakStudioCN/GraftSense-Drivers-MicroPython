"""Conservative async adapters for bounded synchronous bus calls."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from ds1307 import *

class SyncAdapterMixin:
    """Expose explicit async entry points without hiding bus blocking."""

    async def aclose(self):
        deinit = getattr(self, 'deinit', None)
        if deinit is not None:
            deinit()

class DS1307Async(SyncAdapterMixin, DS1307):
    """Explicit accessors for bounded DS1307 I2C property transactions."""

    async def get_datetime_async(self):
        return self.datetime

    async def set_datetime_async(self, value):
        self.datetime = value

    async def get_datetime_rtc_async(self):
        return self.datetimeRTC

    async def get_disable_oscillator_async(self):
        return self.disable_oscillator

    async def set_disable_oscillator_async(self, value):
        self.disable_oscillator = value
