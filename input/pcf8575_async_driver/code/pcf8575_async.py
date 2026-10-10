"""Async-facing PCF8575 adapter with serialized bounded I2C transactions."""

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from pcf8575 import PCF8575


class PCF8575Async(PCF8575):
    """PCF8575 adapter; each I2C transfer remains synchronously bounded."""

    def __init__(self, i2c, address=0x20, interrupt_pin=None, callback=None):
        self._event_pending = False
        self._async_callback = callback
        self._lock = asyncio.Lock()
        self._pending_init = (i2c, address, interrupt_pin)
        self._initialized = False

    async def initialize_async(self):
        if not self._initialized:
            i2c, address, interrupt_pin = self._pending_init
            PCF8575.__init__(self, i2c, address, interrupt_pin, None)
            self._initialized = True

    def _ready(self):
        if not self._initialized:
            raise RuntimeError("call initialize_async() before use")

    def _interrupt_handler(self, pin):
        self._event_pending = True

    async def check_async(self):
        self._ready()
        async with self._lock:
            return self.check()

    async def get_port_async(self):
        self._ready()
        async with self._lock:
            return self.port

    async def set_port_async(self, value):
        self._ready()
        async with self._lock:
            self.port = value

    async def pin_async(self, pin, value=None):
        self._ready()
        async with self._lock:
            return self.pin(pin, value)

    async def toggle_async(self, pin):
        self._ready()
        async with self._lock:
            self.toggle(pin)

    async def dispatch_pending_async(self):
        if not self._event_pending:
            return False
        self._event_pending = False
        if self._async_callback is not None:
            result = self._async_callback(self)
            if hasattr(result, "__await__"):
                await result
        return True

    def deinit(self):
        if self._initialized and self.interrupt_pin is not None:
            self.interrupt_pin.irq(handler=None)
        self._initialized = False

    async def aclose(self):
        self.deinit()
