try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from sht25 import SHT25, _celsius_to_fahrenheit, _clamp_rh


class SHT25Async(SHT25):
    async def _read_measurement_async(self, command, delay_ms, timeout_ms):
        if not isinstance(command, int):
            raise ValueError("command must be int")
        if command < 0 or command > 0xFF:
            raise ValueError("command must be 0~255")
        started = time.ticks_ms()
        try:
            self._i2c.writeto(self._addr, bytes((command,)))
        except OSError as error:
            raise RuntimeError("I2C write command 0x%02X failed" % command) from error
        await asyncio.sleep_ms(delay_ms)
        if time.ticks_diff(time.ticks_ms(), started) > timeout_ms:
            raise RuntimeError("SHT25 measurement timeout")
        try:
            data = self._i2c.readfrom(self._addr, 3)
        except OSError as error:
            raise RuntimeError("I2C read measurement failed") from error
        return ((data[0] << 8) | data[1]) & 0xFFFC

    async def temperature_c_async(self, timeout_ms=200):
        raw = await self._read_measurement_async(self.CMD_TRIGGER_TEMP_NO_HOLD, 90, timeout_ms)
        return -46.85 + 175.72 * raw / 65536.0

    async def temperature_f_async(self, timeout_ms=200):
        return _celsius_to_fahrenheit(await self.temperature_c_async(timeout_ms))

    async def humidity_async(self, timeout_ms=200):
        raw = await self._read_measurement_async(self.CMD_TRIGGER_HUMIDITY_NO_HOLD, 30, timeout_ms)
        return _clamp_rh(-6.0 + 125.0 * raw / 65536.0)

    async def reset_async(self, timeout_ms=100):
        started = time.ticks_ms()
        try:
            self._i2c.writeto(self._addr, bytes((self.CMD_SOFT_RESET,)))
        except OSError as error:
            raise RuntimeError("I2C soft reset failed") from error
        await asyncio.sleep_ms(15)
        if time.ticks_diff(time.ticks_ms(), started) > timeout_ms:
            raise RuntimeError("SHT25 reset timeout")

    async def read_user_register_async(self):
        return super().read_user_register()

    async def write_user_register_async(self, value):
        return super().write_user_register(value)

    def read_user_register(self):
        return super().read_user_register()

    def write_user_register(self, value):
        return super().write_user_register(value)
    async def aclose(self):
        if self._i2c is None:
            return
        try:
            self._i2c.writeto(self._addr, bytes((self.CMD_SOFT_RESET,)))
        except OSError:
            pass
        await asyncio.sleep_ms(15)
        self._i2c = None
        self._addr = None