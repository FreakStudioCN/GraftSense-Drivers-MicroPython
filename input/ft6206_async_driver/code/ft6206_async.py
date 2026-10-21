"""Async FT6206 adapter for bounded touch-register reads."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from ft6206 import FT6206


class FT6206Async(FT6206):
    """FT6206 event bridge; callback work remains outside IRQ context."""

    def __init__(self, i2c, address=FT6206.DEFAULT_ADDR, width=320,
                 height=240, max_touches=2, invert_x=False, invert_y=False,
                 swap_xy=False, callback=None, verify=True, debug=False):
        if not (hasattr(i2c, "readfrom_mem") and hasattr(i2c, "writeto_mem")):
            raise TypeError("i2c must provide readfrom_mem/writeto_mem")
        if not isinstance(address, int) or address < 0x08 or address > 0x77:
            raise ValueError("address must be a valid I2C address (0x08-0x77)")
        if max_touches < 1 or max_touches > 2:
            raise ValueError("max_touches must be 1 or 2")
        if width < 1 or height < 1:
            raise ValueError("width and height must be positive integers")
        if not (isinstance(invert_x, bool) and isinstance(invert_y, bool)
                and isinstance(swap_xy, bool)):
            raise ValueError("invert_x, invert_y, swap_xy must be bool")

        # Construction is inert; this state exists before an IRQ is bound.
        self._irq_pending = False
        self.i2c = i2c
        self.addr = address
        self.width = width
        self.height = height
        self.max_touches = max_touches
        self.invert_x = invert_x
        self.invert_y = invert_y
        self.swap_xy = swap_xy
        self._callback = callback
        self._debug = debug
        self._verify_requested = verify
        self._initialized = False
        self._buf = bytearray(FT6206.BUF_SIZE)
        self._touches = 0
        self._touch_x = [0] * max_touches
        self._touch_y = [0] * max_touches
        self._touch_weight = [0] * max_touches
        self._touch_area = [0] * max_touches

    async def initialize_async(self):
        if self._initialized:
            return
        if self._verify_requested:
            chip_id, _, _, _ = await self.read_chip_id_async()
            self._log("FT6206: chip_id=0x{:02X}".format(chip_id))
        self._initialized = True

    def irq_handler(self, pin):
        self._irq_pending = True

    async def read_chip_id_async(self):
        return (
            await self._read_reg_async(FT6206.REG_FOCALTECH_ID),
            await self._read_reg_async(FT6206.REG_FIRMID),
            await self._read_reg_async(FT6206.REG_LIB_VER_H),
            await self._read_reg_async(FT6206.REG_LIB_VER_L),
        )

    async def read_touch_async(self):
        await self._read_data_async()
        points = []
        for index in range(self._touches):
            points.append((self._touch_x[index], self._touch_y[index],
                           self._touch_weight[index], self._touch_area[index]))
        return self._touches, points

    async def touched_async(self):
        count = await self._read_reg_async(FT6206.REG_TD_STATUS)
        count &= FT6206.TOUCH_COUNT_MASK
        return 0 if count > self.max_touches else count

    async def position_async(self):
        await self._read_data_async()
        return [(self._touch_x[index], self._touch_y[index])
                for index in range(self._touches)]

    async def _read_reg_async(self, reg):
        for attempt in range(FT6206.MAX_I2C_RETRIES):
            try:
                return self.i2c.readfrom_mem(self.addr, reg, 1)[0]
            except OSError:
                if attempt == FT6206.MAX_I2C_RETRIES - 1:
                    raise OSError("I2C read reg 0x{:02X} failed after {} retries".format(
                        reg, FT6206.MAX_I2C_RETRIES
                    ))
                await asyncio.sleep_ms(1)

    async def _read_data_async(self):
        for attempt in range(FT6206.MAX_I2C_RETRIES):
            try:
                self.i2c.readfrom_mem_into(self.addr, 0x00, self._buf)
                break
            except OSError:
                if attempt == FT6206.MAX_I2C_RETRIES - 1:
                    self._touches = 0
                    return
                await asyncio.sleep_ms(1)

        self._touches = self._buf[FT6206.REG_TD_STATUS] & FT6206.TOUCH_COUNT_MASK
        if self._touches > self.max_touches:
            self._touches = 0
        for index in range(self._touches):
            base = FT6206.REG_P1_XH + index * 6
            x = ((self._buf[base] & 0x0F) << 8) | self._buf[base + 1]
            y = ((self._buf[base + 2] & 0x0F) << 8) | self._buf[base + 3]
            if self.swap_xy:
                x, y = y, x
            if self.invert_x:
                x = self.width - 1 - x
            if self.invert_y:
                y = self.height - 1 - y
            self._touch_x[index] = x
            self._touch_y[index] = y
            self._touch_weight[index] = self._buf[base + 4]
            self._touch_area[index] = self._buf[base + 5] & 0x0F
        if self._touches == 0:
            for index in range(self.max_touches):
                self._touch_x[index] = 0
                self._touch_y[index] = 0
                self._touch_weight[index] = 0
                self._touch_area[index] = 0

    async def service_irq_async(self):
        if not getattr(self, "_irq_pending", False):
            return None
        self._irq_pending = False
        data = await self.read_touch_async()
        if self._callback is not None:
            # Preserve the source callback signature: x-list, y-list, count.
            self._callback(self._touch_x, self._touch_y, self._touches)
        return data

    async def aclose(self):
        FT6206.deinit(self)
