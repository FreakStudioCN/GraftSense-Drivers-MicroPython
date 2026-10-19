"""Async GT911 adapter with cooperative reset timing."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from _gs_gt911_gt911 import GT911, Pin
from array import array


class GT911Async(GT911):
    """GT911 event bridge; I2C configuration accesses are bounded operations."""

    def __init__(self, i2c, int_pin, rst_pin, addr=0x5D, width=240,
                 height=320, touch_points=2, reverse_x=False,
                 reverse_y=False, reverse_axis=False, sito=False,
                 refresh_rate=240, user_callback=None):
        if addr not in (0x5D, 0x14):
            raise ValueError("GT911 I2C address must be 0x5D or 0x14")
        if not hasattr(i2c, "readfrom_mem") or touch_points > 5:
            raise ValueError("invalid I2C bus or touch-point count")
        if user_callback is not None and not callable(user_callback):
            raise ValueError("user_callback must be callable")
        self.i2c = i2c
        self.addr = addr
        self.int_pin_label = int_pin
        self.rst_pin_label = rst_pin
        self.rst_pin = None
        self.int_pin = None
        self.user_callback = user_callback
        self._width = width
        self._height = height
        self._touch_points = touch_points
        self._switch = (int(reverse_y) << 7) | (int(reverse_x) << 6) | (int(reverse_axis) << 3) | (int(sito) << 2) | 0x01
        self._refresh_rate = refresh_rate
        self.points_data = [array("H", [0, 0, 0, 0]) for _ in range(5)]
        self._irq_pending = False
        self._initialized = False

    async def initialize_async(self):
        if self._initialized:
            return
        await self.reset_async()
        GT911._write_reg(self, GT911.RESOLUTION_X, self._width, 2)
        GT911._write_reg(self, GT911.RESOLUTION_Y, self._height, 2)
        GT911._write_reg(self, GT911.TOUCH_POINTS, self._touch_points)
        GT911._write_reg(self, GT911.MODULE_SWITCH1, self._switch)
        GT911._write_reg(self, GT911.REFRESH_RATE, (1000000 // (self._refresh_rate * 250)))
        GT911._write_reg(self, GT911.COMMAND, 0)
        GT911.reflash_config(self)
        if self.user_callback is not None:
            self.int_pin.irq(trigger=Pin.IRQ_FALLING, handler=self.irq_callback)
        self._initialized = True

    async def reset_async(self):
        self.rst_pin = Pin(self.rst_pin_label, Pin.OUT, value=0)
        int_pin = Pin(self.int_pin_label, Pin.OUT)
        int_pin.value(0 if self.addr == 0x5D else 1)
        await asyncio.sleep_ms(11)
        self.rst_pin.value(1)
        await asyncio.sleep_ms(55)
        self.int_pin = Pin(self.int_pin_label, Pin.IN)
        await asyncio.sleep_ms(100)

    async def reflash_config_async(self):
        return GT911.reflash_config(self)

    async def read_touch_async(self):
        return GT911.read_touch(self)

    async def available_async(self):
        return GT911.available(self)

    async def read_id_async(self):
        return GT911.read_id(self)

    def irq_callback(self, pin):
        self._irq_pending = True

    async def service_irq_async(self):
        if not self._irq_pending:
            return None
        self._irq_pending = False
        touches = GT911.read_touch(self)
        if self.user_callback is not None:
            self.user_callback(touches)
        return touches

    async def aclose(self):
        if getattr(self, "int_pin", None) is not None:
            self.int_pin.irq(handler=None)
        self.user_callback = None
        self.i2c = None
