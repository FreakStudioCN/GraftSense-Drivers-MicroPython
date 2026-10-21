
# Preserve the documented exception contract on MicroPython.
try:
    TimeoutError
except NameError:
    try:
        from uasyncio import TimeoutError
    except ImportError:
        from asyncio import TimeoutError

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from sht35 import SHT35, REPEATABILITY_HIGH, _sht35_check_crc


class SHT35Async(SHT35):
    """SHT35 command/write, cooperative conversion delay, and read adapter."""

    async def reset_async(self):
        self._write_command(b"\x30\xa2")
        await asyncio.sleep_ms(2)

    async def read_raw_async(
        self,
        repeatability=REPEATABILITY_HIGH,
        clock_stretch=False,
        check_crc=True,
        timeout_ms=50,
    ):
        if repeatability not in self._MEASURE_COMMANDS[clock_stretch]:
            raise ValueError("invalid repeatability: %d" % repeatability)
        self._write_command(self._MEASURE_COMMANDS[clock_stretch][repeatability])
        started = time.ticks_ms()
        delay = self._MEASURE_DELAYS_MS[repeatability]
        while time.ticks_diff(time.ticks_ms(), started) < delay:
            if time.ticks_diff(time.ticks_ms(), started) >= timeout_ms:
                raise TimeoutError("SHT35 measurement timed out")
            await asyncio.sleep_ms(1)
        data = self._read(6)
        if check_crc:
            if not _sht35_check_crc(data[0:2], data[2]):
                raise RuntimeError("SHT35 temperature CRC check failed")
            if not _sht35_check_crc(data[3:5], data[5]):
                raise RuntimeError("SHT35 humidity CRC check failed")
        return ((data[0] << 8) | data[1], (data[3] << 8) | data[4])

    async def read_status_async(self):
        return self.read_status()

    async def measure_async(self, repeatability=REPEATABILITY_HIGH, clock_stretch=False, celsius=True, check_crc=True, timeout_ms=50):
        temperature_ticks, humidity_ticks = await self.read_raw_async(repeatability, clock_stretch, check_crc, timeout_ms)
        temperature = -45 + (175 * temperature_ticks / 65535) if celsius else -49 + (315 * temperature_ticks / 65535)
        return temperature, 100 * humidity_ticks / 65535

    async def deinit_async(self):
        super().deinit()
        await asyncio.sleep_ms(0)

    async def aclose(self):
        await self.deinit_async()
