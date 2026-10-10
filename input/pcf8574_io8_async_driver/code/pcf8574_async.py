"""Async PCF8574 adapter for bounded one-byte I2C operations."""
from pcf8574 import PCF8574


class PCF8574Async(PCF8574):
    """PCF8574 adapter; no I2C work is performed in the IRQ handler."""

    async def check_async(self):
        return PCF8574.check(self)

    async def get_port_async(self):
        return self.port

    async def set_port_async(self, value):
        self.port = value

    async def pin_async(self, pin, value=None):
        return PCF8574.pin(self, pin, value)

    async def toggle_async(self, pin):
        return PCF8574.toggle(self, pin)

    async def aclose(self):
        if getattr(self, "_int_pin", None) is not None:
            self._int_pin.irq(handler=None)
        self._callback = None
        self._i2c = None
