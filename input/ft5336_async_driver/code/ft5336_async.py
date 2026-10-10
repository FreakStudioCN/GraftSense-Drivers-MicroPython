"""Async FT5336 adapter for bounded I2C transactions."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import ft5336 as _sync
from ft5336 import FT5336


class FT5336Async(FT5336):
    """FT5336 sync-adapter-only API with source-compatible calls."""

    async def _read_data_async(self):
        buffer = self._read_buffer
        for attempt in range(3):
            try:
                self.i2c.readfrom_mem_into(self.i2c_addr, 0x00, buffer)
                break
            except OSError as error:
                if attempt == 2:
                    raise RuntimeError("I2C read failed when reading touch data block") from error
                await asyncio.sleep_ms(10)
        self._touches = buffer[_sync._TD_STATUS]
        if self._touches > self.max_touches or self._touches == 0:
            self._touches = 0
            return
        for index in range(self._touches):
            x = (buffer[_sync._TOUCH1_XH + index * 6] & 0x0F) << 8 | buffer[_sync._TOUCH1_XL + index * 6]
            y = (buffer[_sync._TOUCH1_YH + index * 6] & 0x0F) << 8 | buffer[_sync._TOUCH1_YL + index * 6]
            if self._invert_x:
                x = self._screen_width - 1 - x
            if self._invert_y:
                y = self._screen_height - 1 - y
            if self._swap_xy:
                x, y = y, x
            self._touch_x[index] = x
            self._touch_y[index] = y
            self._touch_id[index] = buffer[_sync._TOUCH1_YH + index * 6] >> 4

    async def touches_async(self):
        await self._read_data_async()
        return [(self._touch_x[index], self._touch_y[index], 1) for index in range(self._touches)]

    async def point_async(self, point_index):
        if not isinstance(point_index, int):
            raise TypeError("point_index must be an integer")
        await self._read_data_async()
        if point_index >= self._touches:
            return (0, 0, 0)
        return (self._touch_x[point_index], self._touch_y[point_index], 1)

    async def touched_async(self):
        for attempt in range(3):
            try:
                value = self.i2c.readfrom_mem(self.i2c_addr, _sync._REG_NUMTOUCHES, 1)[0]
                return 0 if value > self.max_touches else value
            except OSError as error:
                if attempt == 2:
                    raise RuntimeError("I2C read failed at register 0x%02X" % _sync._REG_NUMTOUCHES) from error
                await asyncio.sleep_ms(10)

    async def points_async(self):
        return await self.touches_async()

    async def get_invert_x_async(self):
        return self.invert_x

    async def set_invert_x_async(self, value):
        self.invert_x = value

    async def get_invert_y_async(self):
        return self.invert_y

    async def set_invert_y_async(self, value):
        self.invert_y = value

    async def get_swap_xy_async(self):
        return self.swap_xy

    async def set_swap_xy_async(self, value):
        self.swap_xy = value

    async def aclose(self):
        FT5336.deinit(self)
