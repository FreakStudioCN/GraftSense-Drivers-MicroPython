"""Async facade for bounded MCP4728 I2C transactions."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import mcp4728 as _source


class ChannelAsync:
    def __init__(self, channel, lock):
        self._channel = channel
        self._lock = lock

    async def get_normalized_value_async(self):
        async with self._lock:
            return self._channel.normalized_value

    async def set_normalized_value_async(self, value):
        async with self._lock:
            self._channel.normalized_value = value

    async def get_value_async(self):
        async with self._lock:
            return self._channel.value

    async def set_value_async(self, value):
        async with self._lock:
            self._channel.value = value

    async def get_gain_async(self):
        async with self._lock:
            return self._channel.gain

    async def set_gain_async(self, value):
        async with self._lock:
            self._channel.gain = value

    async def get_vref_async(self):
        async with self._lock:
            return self._channel.vref

    async def set_vref_async(self, value):
        async with self._lock:
            self._channel.vref = value

    async def get_pdm_async(self):
        async with self._lock:
            return self._channel.pdm

    async def set_pdm_async(self, value):
        async with self._lock:
            self._channel.pdm = value

    async def config_async(self, value=0, vref=1, gain=1, pdm=0):
        async with self._lock:
            return self._channel.config(value, vref, gain, pdm)


class MCP4728Async:
    def __init__(self, i2c_bus, address=0x60):
        self._driver = _source.MCP4728(i2c_bus, address)
        self._lock = asyncio.Lock()
        self.a = ChannelAsync(self._driver.a, self._lock)
        self.b = ChannelAsync(self._driver.b, self._lock)
        self.c = ChannelAsync(self._driver.c, self._lock)
        self.d = ChannelAsync(self._driver.d, self._lock)

    async def save_settings_async(self):
        async with self._lock:
            values = []
            for channel in (self._driver.a, self._driver.b, self._driver.c, self._driver.d):
                values += self._driver._generate_bytes_with_flags(channel)
            self._driver.i2c_device.writeto(self._driver.address, bytearray([0x50] + values))
            await asyncio.sleep_ms(15)

    async def sync_vrefs_async(self):
        async with self._lock:
            return self._driver.sync_vrefs()

    async def sync_gains_async(self):
        async with self._lock:
            return self._driver.sync_gains()

    async def sync_pdms_async(self):
        async with self._lock:
            return self._driver.sync_pdms()

    async def aclose(self):
        return None

