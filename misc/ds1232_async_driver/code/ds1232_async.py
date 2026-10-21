try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin


class DS1232Async:
    """Task-based DS1232 feeder; Pin writes never occur in a Timer IRQ."""
    def __init__(self, wdi_pin, feed_interval=1000):
        if not isinstance(wdi_pin, int):
            raise ValueError("wdi pin must be an integer")
        if feed_interval <= 0 or feed_interval > 1000:
            raise ValueError("feed_interval must be 1-1000ms")
        self._wdi_pin = wdi_pin
        self.wdi = None
        self.feed_interval = feed_interval
        self.state = 0
        self._task = None

    async def initialize_async(self):
        """Create the WDI output and start the source-equivalent feeder."""
        if self.wdi is None:
            self.wdi = Pin(self._wdi_pin, Pin.OUT)
            self.wdi.value(0)
        await self.start_async()

    def _feed_once(self):
        if self.wdi is None:
            raise RuntimeError("call initialize_async() before feeding DS1232")
        self.state ^= 1
        self.wdi.value(self.state)

    async def _feed_loop(self):
        try:
            while True:
                await asyncio.sleep_ms(self.feed_interval)
                self._feed_once()
        finally:
            if self.wdi is not None:
                self.wdi.value(0)

    async def start_async(self):
        if self.wdi is None:
            await self.initialize_async()
            return
        if self._task is None:
            self._task = asyncio.create_task(self._feed_loop())

    async def stop_async(self):
        task, self._task = self._task, None
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        if self.wdi is not None:
            self.wdi.value(0)

    async def kick_async(self):
        self._feed_once()

    async def aclose(self):
        await self.stop_async()
