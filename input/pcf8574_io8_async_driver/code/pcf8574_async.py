"""Async PCF8574 adapter for bounded one-byte I2C operations."""
from _gs_pcf8574_io8_pcf8574 import PCF8574


class PCF8574Async(PCF8574):
    """PCF8574 adapter; no I2C work is performed in the IRQ handler."""

    def __init__(self, *args, **kwargs):
        self._irq_pending = False
        self._irq_dropped = False
        super().__init__(*args, **kwargs)

    async def dispatch_pending_async(self):
        """Read and dispatch the source callback(port) in the owning task."""
        if not self._irq_pending and not self._irq_dropped:
            return False
        self._irq_pending = self._irq_dropped = False
        value = self.port
        if self._callback is not None:
            result = self._callback(value)
            if hasattr(result, "send") or hasattr(result, "__await__"):
                await result
        return True

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
        self._irq_pending = self._irq_dropped = False
        self._i2c = None
