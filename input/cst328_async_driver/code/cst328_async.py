import time
"""Conservative async adapters for bounded synchronous bus calls."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from cst328 import *
import machine


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


class SyncAdapterMixin:
    """Expose explicit async entry points without hiding bus blocking."""

    async def aclose(self):
        deinit = getattr(self, 'deinit', None)
        if deinit is not None:
            deinit()

class CST328Async(SyncAdapterMixin, CST328):
    """Async facade; each delegated call remains a short sync transaction."""

    def __init__(self, i2c, address=0x1A, rst_pin=None, irq_pin=None,
                 callback=None, trigger=machine.Pin.IRQ_FALLING, width=320,
                 height=240, debug=False):
        if not hasattr(i2c, "writeto") or not hasattr(i2c, "readfrom"):
            raise ValueError("i2c must provide writeto() and readfrom()")
        if not isinstance(address, int) or not 0x08 <= address <= 0x77:
            raise ValueError("address must be 0x08~0x77")
        if rst_pin is not None and not hasattr(rst_pin, "value"):
            raise ValueError("rst_pin must be a Pin instance or None")
        if irq_pin is not None and not hasattr(irq_pin, "irq"):
            raise ValueError("irq_pin must be a Pin instance or None")
        if callback is not None and not callable(callback):
            raise ValueError("callback must be callable or None")
        if not isinstance(width, int) or width <= 0 or not isinstance(height, int) or height <= 0:
            raise ValueError("width and height must be positive int")
        self._i2c, self._address = i2c, address
        self._rst_pin, self._irq_pin, self._callback, self._trigger = rst_pin, irq_pin, callback, trigger
        self._width, self._height, self._debug = width, height, bool(debug)
        self._triggered, self._initialized = True, False

    def _irq_bridge(self, pin):
        """Hard IRQ path: only retain an already-allocated event flag."""
        self._triggered = True

    async def initialize_async(self):
        if self._initialized:
            return
        if self._rst_pin is not None:
            await self.reset_async()
        if self._irq_pin is not None:
            self._irq_pin.irq(handler=self._irq_bridge, trigger=self._trigger)
        self._initialized = True

    async def reset_async(self):
        if self._rst_pin is None:
            raise RuntimeError("Reset pin is not configured")
        self._rst_pin.value(1)
        await asyncio.sleep_ms(10)
        await _pulse_low_async(self._rst_pin, 10)
        await asyncio.sleep_ms(100)
        self._triggered = True

    async def touched_async(self):
        return await self.read_point_async() is not None

    async def read_point_async(self):
        state = machine.disable_irq()
        triggered = self._triggered
        self._triggered = False
        machine.enable_irq(state)
        if not triggered and self._irq_pin is not None:
            return None
        if triggered and self._callback is not None:
            self._callback(self._irq_pin)
        for attempt in range(2):
            try:
                self._i2c.writeto(self._address, bytes((0xD0, 0x00)), False)
                data = self._i2c.readfrom(self._address, self._TOUCH_DATA_LEN)
                break
            except OSError:
                if attempt:
                    return None
                await asyncio.sleep_ms(5)
        if (data[0] & self._GESTURE_MASK) != self._GESTURE_VALID:
            return None
        return {"x": (data[1] << 4) | ((data[3] >> 4) & 0x0F), "y": (data[2] << 4) | (data[3] & 0x0F)}

    async def set_size_async(self, width, height):
        return self.set_size(width, height)

    async def get_size_async(self):
        return self.get_size()

    async def set_debug_async(self, debug):
        return self.set_debug(debug)

    def deinit(self):
        if self._irq_pin is not None:
            self._irq_pin.irq(handler=None)
        self._initialized = False

    async def deinit_async(self):
        self.deinit()

    async def aclose(self):
        await self.deinit_async()
