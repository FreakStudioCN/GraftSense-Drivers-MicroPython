"""Async FT6x06 adapter for bounded touch-register reads."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from ft6x06 import (
    FT6x06, _DEFAULT_ADDR, _REG_TD_STATUS, _TOUCH_DATA_START,
    _TOUCH_DATA_SIZE, _TOUCH_EVENT_SHIFT, _COORD_HIGH_MASK, _AREA_SHIFT,
    _DEFAULT_RETRIES, _DEFAULT_RETRY_DELAY_MS, Pin,
)


class FT6x06Async(FT6x06):
    """FT6x06 event bridge with explicit API signatures."""

    def __init__(self, i2c, *, address=_DEFAULT_ADDR, interrupt_pin=None,
                 callback=None, trigger=Pin.IRQ_FALLING, debug=False):
        # The source constructor may register self._irq_handler immediately.
        self._irq_pending = False
        FT6x06.__init__(
            self, i2c, address=address, interrupt_pin=interrupt_pin,
            callback=callback, trigger=trigger, debug=debug
        )

    def _irq_handler(self, pin):
        # Hard IRQ: only coalesce into preallocated state.
        self._irq_pending = True

    def _process_touch_irq(self, _):
        # Defensive soft-IRQ entry: no I/O or callback in scheduled context.
        self._irq_pending = True

    async def get_touch_coords_async(self):
        touches = await self.get_touch_count_async()
        if touches == 0:
            return None
        touch_data = []
        for index in range(touches):
            event = await self.get_coords_for_p_async(index)
            touch_data.append({
                "x": event[0], "y": event[1],
                "type": "down" if event[2] == 0 else "up",
                "weight": event[3], "area": event[4],
            })
        return touch_data

    async def get_touch_count_async(self):
        return (await self._get_reg_async(_REG_TD_STATUS)) & 7

    async def get_coords_for_p_async(self, touch_id):
        if not isinstance(touch_id, int):
            raise TypeError("touch_id must be an integer")
        data = await self._get_reg_async(
            _TOUCH_DATA_START + (_TOUCH_DATA_SIZE * touch_id), 6
        )
        return (
            ((data[0] & _COORD_HIGH_MASK) << 8) | data[1],
            ((data[2] & _COORD_HIGH_MASK) << 8) | data[3],
            data[0] >> _TOUCH_EVENT_SHIFT,
            data[4], data[5] >> _AREA_SHIFT,
        )

    async def get_reg_async(self, register, count=1):
        return await self._get_reg_async(register, count)

    async def _get_reg_async(self, register, count=1):
        for attempt in range(_DEFAULT_RETRIES):
            try:
                if count == 1:
                    return self.i2c.readfrom_mem(self.i2c_addr, register, 1)[0]
                return self.i2c.readfrom_mem(self.i2c_addr, register, count)
            except OSError as error:
                if attempt == _DEFAULT_RETRIES - 1:
                    raise RuntimeError(
                        "I2C read failed at register 0x{:02X}".format(register)
                    ) from error
                await asyncio.sleep_ms(_DEFAULT_RETRY_DELAY_MS)

    async def service_irq_async(self):
        if not getattr(self, "_irq_pending", False):
            return None
        self._irq_pending = False
        data = await self.get_touch_coords_async()
        if data is not None and self._callback is not None:
            self._callback(data)
        return data

    async def aclose(self):
        FT6x06.deinit(self)
