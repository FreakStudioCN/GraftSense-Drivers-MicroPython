"""Conservative async adapters for bounded synchronous bus calls."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from pcf85063 import *

class SyncAdapterMixin:
    """Expose explicit async entry points without hiding bus blocking."""

    async def aclose(self):
        deinit = getattr(self, 'deinit', None)
        if deinit is not None:
            deinit()

class PCF85063Async(SyncAdapterMixin, PCF85063):
    """Async facade; each delegated call remains a short sync transaction."""

    async def _read_reg_async(self, reg, nbytes, retries=2, delay_ms=5):
        buf = bytearray(nbytes)
        for attempt in range(retries + 1):
            try:
                self._i2c.readfrom_mem_into(self._addr, reg, buf)
                return buf
            except OSError:
                if attempt == retries:
                    raise RuntimeError("I2C read failed at reg 0x%02X after %d retries" % (reg, retries))
                await asyncio.sleep_ms(delay_ms)

    async def _write_reg_async(self, reg, data, retries=2, delay_ms=5):
        for attempt in range(retries + 1):
            try:
                self._i2c.writeto_mem(self._addr, reg, data)
                return
            except OSError:
                if attempt == retries:
                    raise RuntimeError("I2C write failed at reg 0x%02X after %d retries" % (reg, retries))
                await asyncio.sleep_ms(delay_ms)

    async def reset_async(self):
        self._log("performing soft reset")
        await self._write_reg_async(REG_CTRL1, b"\x58")

    async def datetime_async(self, value=None):
        if value is None:
            return await self.read_datetime_async()
        await self.set_datetime_async(value)

    async def set_datetime_async(self, value):
        if value is None or not isinstance(value, (tuple, list)) or len(value) < 7:
            raise ValueError("value must be a datetime tuple or list with at least 7 elements")
        year, month, day, weekday, hour, minute, second = value[:7]
        data = bytes((self._dec_to_bcd(second), self._dec_to_bcd(minute), self._dec_to_bcd(hour), self._dec_to_bcd(day), self._dec_to_bcd(weekday), self._dec_to_bcd(month), self._dec_to_bcd(year - self._year_base)))
        self._log("setting datetime: %s" % str(value[:7]))
        await self._write_reg_async(REG_SECONDS, data)

    async def read_datetime_async(self):
        buf = await self._read_reg_async(REG_SECONDS, 7)
        result = (self._bcd_to_dec(buf[6]) + self._year_base, self._bcd_to_dec(buf[5] & 0x1F), self._bcd_to_dec(buf[3] & 0x3F), self._bcd_to_dec(buf[4] & 0x07), self._bcd_to_dec(buf[2] & 0x3F), self._bcd_to_dec(buf[1] & 0x7F), self._bcd_to_dec(buf[0] & 0x7F))
        self._log("read datetime: %s" % str(result))
        return result

    async def set_alarm_async(self, second=ALARM_DISABLE, minute=ALARM_DISABLE, hour=ALARM_DISABLE, day=ALARM_DISABLE, weekday=ALARM_DISABLE):
        data = bytes((self._alarm_value(second, 0, 59), self._alarm_value(minute, 0, 59), self._alarm_value(hour, 0, 23), self._alarm_value(day, 1, 31), self._alarm_value(weekday, 0, 6)))
        await self._write_reg_async(REG_ALARM_SECONDS, data)

    async def enable_alarm_interrupt_async(self, enable=True):
        value = (await self._read_reg_async(REG_CTRL2, 1))[0]
        value = (value | 0x80) & ~0x40 if enable else value & ~0x80
        await self._write_reg_async(REG_CTRL2, bytes([value]))

    async def deinit_async(self):
        await self.enable_alarm_interrupt_async(False)
        self._i2c = None
        self._addr = None

    async def aclose(self):
        await self.deinit_async()

    @staticmethod
    def _dec_to_bcd(value):
        return ((value // 10) << 4) | (value % 10)

    @staticmethod
    def _bcd_to_dec(value):
        return ((value >> 4) * 10) + (value & 0x0F)
