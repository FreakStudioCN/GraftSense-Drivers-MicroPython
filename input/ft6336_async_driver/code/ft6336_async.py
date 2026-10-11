"""Async FT6336 adapter with cooperative hardware-reset timing."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from ft6336 import FT6336


class FT6336Async(FT6336):
    """FT6336 event bridge; each register operation is bounded I2C work."""

    def __init__(self, i2c, address=None, reset_pin=None, irq_pin=None,
                 callback=None, trigger=0, gesture=False, verify=False,
                 debug=False):
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must provide readfrom_mem()")
        if address is not None and (not isinstance(address, int) or not 0 <= address <= 127):
            raise ValueError("address must be 0x00~0x7f")
        if reset_pin is not None and not hasattr(reset_pin, "value"):
            raise ValueError("reset_pin must be a Pin instance")
        if irq_pin is not None and not hasattr(irq_pin, "irq"):
            raise ValueError("irq_pin must be a Pin instance")
        if callback is not None and not callable(callback):
            raise ValueError("callback must be callable")
        self._i2c = i2c
        self._addr = self.DEFAULT_ADDRESS if address is None else address
        self._reset_pin = reset_pin
        self._irq_pin = irq_pin
        self._callback = callback
        self._trigger = 2 if trigger == 0 else trigger
        self._gesture_requested = gesture
        self._verify_requested = verify
        self._debug = debug
        self._triggered = False
        self._point = None
        self._buf4 = bytearray(4)
        self._initialized = False

    async def initialize_async(self):
        if self._initialized:
            return
        if self._reset_pin is not None:
            await self.reset_async()
        else:
            self._triggered = True
        FT6336.enable_gesture(self, self._gesture_requested)
        if self._verify_requested and FT6336.read_chip_id(self) != self.EXPECTED_CHIP_ID:
            raise RuntimeError("FT6336 chip id mismatch")
        if self._irq_pin is not None:
            self._irq_pin.irq(handler=self._irq_handler, trigger=self._trigger)
        self._initialized = True

    async def reset_async(self):
        if self._reset_pin is None:
            raise RuntimeError("Reset pin not configured")
        self._reset_pin.value(1)
        await asyncio.sleep_ms(self._RESET_DELAY_MS)
        self._reset_pin.value(0)
        await asyncio.sleep_ms(self._RESET_DELAY_MS)
        self._reset_pin.value(1)
        await asyncio.sleep_ms(self._RESET_DELAY_MS)
        self._triggered = True

    async def read_chip_id_async(self):
        return FT6336.read_chip_id(self)

    async def enable_gesture_async(self, enable=True):
        return FT6336.enable_gesture(self, enable)

    async def get_touch_count_async(self):
        return FT6336.get_touch_count(self)

    async def read_point_async(self):
        return FT6336.read_point(self)

    async def get_gesture_async(self):
        return FT6336.get_gesture(self)

    async def service_irq_async(self):
        """Consume one IRQ notification and invoke the callback outside ISR."""
        if not self._triggered:
            return None
        point = FT6336.read_point(self)
        if point is not None and self._callback is not None:
            self._callback(point)
        return point

    async def aclose(self):
        if self._irq_pin is not None:
            self._irq_pin.irq(handler=None)
        self._callback = None
        self._i2c = None
