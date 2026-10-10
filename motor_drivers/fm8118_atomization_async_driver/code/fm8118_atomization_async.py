"""Conservative async adapters for bounded synchronous bus calls."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin

class FM8118_AtomizationAsync:
    """Async-only FM8118 GPIO controller preserving its shutdown waveform."""

    def __init__(self, pin):
        self._pin = Pin(pin, Pin.OUT)
        self._pin.value(1)
        self._state = False
        self._closed = False

    async def on_async(self):
        if self._closed: raise RuntimeError("atomizer is closed")
        self._pin.value(0)
        self._state = True

    async def off_async(self):
        if self._closed: return
        self._pin.value(1)
        await asyncio.sleep_ms(100)
        self._pin.value(0)
        await asyncio.sleep_ms(100)
        self._pin.value(1)
        self._state = False

    async def toggle_async(self):
        if self._state:
            return await self.off_async()
        return await self.on_async()

    async def is_on_async(self):
        return self._state

    async def aclose(self):
        if self._closed: return
        try:
            await self.off_async()
        finally:
            self._closed = True
