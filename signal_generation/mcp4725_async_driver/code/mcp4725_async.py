"""Conservative async adapters for bounded synchronous bus calls."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from mcp4725 import MCP4725


class MCP4725Async:
    """Locked async boundary for finite MCP4725 I2C transactions."""
    def __init__(self, i2c, address=0x60):
        self._driver = MCP4725(i2c, address)
        self._lock = asyncio.Lock()
        self._closed = False

    async def write_async(self, value):
        async with self._lock:
            return self._driver.write(value)

    async def read_async(self):
        async with self._lock:
            return self._driver.read()

    async def config_async(self, power_down="Off", value=0, eeprom=False):
        async with self._lock:
            return self._driver.config(power_down, value, eeprom)

    async def aclose(self):
        self._closed = True

