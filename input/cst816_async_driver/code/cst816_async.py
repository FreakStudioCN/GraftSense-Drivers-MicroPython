import time
"""Async CST816 adapter with cooperative reset delays."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from cst816 import CST816, DEFAULT_ADDRESS



async def _pulse_low_async(pin, delay_ms):
    pin.value(0)
    started = time.ticks_ms()
    try:
        await asyncio.sleep_ms(delay_ms)
    finally:
        try:
            remaining = delay_ms - time.ticks_diff(time.ticks_ms(), started)
            while remaining > 0:
                try:
                    await asyncio.sleep_ms(remaining)
                except asyncio.CancelledError:
                    pass
                remaining = delay_ms - time.ticks_diff(time.ticks_ms(), started)
        finally:
            pin.value(1)


class CST816Async(CST816):
    """CST816 event bridge; each register operation is one bounded I2C call."""

    def __init__(self, i2c, address=DEFAULT_ADDRESS, reset_pin=None,
                 irq_pin=None, callback=None, trigger=None, width=240,
                 height=240, debug=False):
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must provide readfrom_mem()")
        if not 0 <= address <= 127 or width <= 0 or height <= 0:
            raise ValueError("invalid address or display dimensions")
        if reset_pin is not None and not hasattr(reset_pin, "value"):
            raise ValueError("reset_pin must be a Pin instance")
        if irq_pin is not None and not hasattr(irq_pin, "irq"):
            raise ValueError("irq_pin must be a Pin instance")
        if callback is not None and not callable(callback):
            raise ValueError("callback must be callable")
        self._i2c = i2c
        self._addr = address
        self._reset_pin = reset_pin
        self._irq_pin = irq_pin
        self._width = width
        self._height = height
        self._debug = debug
        self._callback = callback
        self._trigger = 2 if trigger is None else trigger
        self._triggered = False
        self._initialized = False

    async def initialize_async(self):
        if self._initialized:
            return
        if self._reset_pin is not None:
            await self.reset_async()
        else:
            self._triggered = True
        if self._irq_pin is not None:
            self._irq_pin.irq(handler=self._irq_handler, trigger=self._trigger)
        self._initialized = True

    async def reset_async(self):
        if self._reset_pin is None:
            raise ValueError("No reset pin configured")
        await _pulse_low_async(self._reset_pin, 5)
        await asyncio.sleep_ms(50)
        self._triggered = True

    async def read_chip_id_async(self):
        return CST816.read_chip_id(self)

    async def read_revision_async(self):
        return CST816.read_revision(self)

    async def get_touch_count_async(self):
        return CST816.get_touch_count(self)

    async def get_gesture_async(self):
        return CST816.get_gesture(self)

    async def read_point_async(self):
        return CST816.read_point(self)

    async def touched_async(self):
        return CST816.touched(self)

    async def service_irq_async(self):
        if not self._triggered:
            return None
        point = CST816.read_point(self)
        if point is not None and self._callback is not None:
            self._callback(point)
        return point

    async def aclose(self):
        if self._irq_pin is not None:
            self._irq_pin.irq(handler=None)
        self._callback = None
        self._i2c = None

    async def deinit_async(self):
        await self.aclose()
