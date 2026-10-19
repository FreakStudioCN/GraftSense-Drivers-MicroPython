import time
"""Cooperative SI4732 command driver.

The hardware protocol remains a sequence of bounded I2C transactions. CTS
polling, retry backoff and documented settling periods yield to uasyncio.
"""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

try:
    from time import ticks_ms, ticks_diff
except ImportError:
    import time
    ticks_ms = lambda: int(time.time() * 1000)
    ticks_diff = lambda now, then: now - then

from si4732 import SI4732



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


class SI4732Async(SI4732):
    """SI4732 with explicit cooperative counterparts for bus operations."""

    def __init__(self, i2c, address=0x63, reset_pin=None, timeout_ms=1000, debug=False):
        SI4732.__init__(self, i2c, address, reset_pin, timeout_ms, debug)
        self._command_lock = asyncio.Lock()

    async def reset_async(self):
        if self._reset_pin is None:
            return
        await _pulse_low_async(self._reset_pin, 10)
        await asyncio.sleep_ms(10)

    async def _wait_cts_unlocked(self, timeout_ms=None):
        if timeout_ms is None:
            timeout_ms = self._timeout_ms
        start = ticks_ms()
        while ticks_diff(ticks_ms(), start) < timeout_ms:
            try:
                self._i2c.readfrom_into(self._address, self._status)
            except OSError as exc:
                raise RuntimeError("SI4732 I2C status read failed addr=0x%02X" % self._address) from exc
            status = self._status[0]
            if status & self._STATUS_CTS:
                if status & self._STATUS_ERR:
                    raise RuntimeError("SI4732 reported ERR in status byte 0x%02X" % status)
                return status
            await asyncio.sleep_ms(2)
        raise RuntimeError("SI4732 CTS timeout addr=0x%02X" % self._address)

    async def wait_cts_async(self, timeout_ms=None):
        async with self._command_lock:
            return await self._wait_cts_unlocked(timeout_ms)

    async def _i2c_write_with_retry_async(self, data):
        last_exc = None
        for attempt in range(self._retry_count):
            try:
                self._i2c.writeto(self._address, data)
                return
            except OSError as exc:
                last_exc = exc
                if attempt < self._retry_count - 1:
                    await asyncio.sleep_ms(1)
        raise RuntimeError("SI4732 I2C write failed addr=0x%02X after %d retries" % (self._address, self._retry_count)) from last_exc

    async def _i2c_read_with_retry_async(self, data):
        last_exc = None
        for attempt in range(self._retry_count):
            try:
                self._i2c.readfrom_into(self._address, data)
                return
            except OSError as exc:
                last_exc = exc
                if attempt < self._retry_count - 1:
                    await asyncio.sleep_ms(1)
        raise RuntimeError("SI4732 I2C read failed addr=0x%02X after %d retries" % (self._address, self._retry_count)) from last_exc

    async def _read_response_unlocked(self, length):
        await self._wait_cts_unlocked()
        data = bytearray(length)
        await self._i2c_read_with_retry_async(data)
        if data and data[0] & self._STATUS_ERR:
            raise RuntimeError("SI4732 response has ERR bit set: 0x%02X" % data[0])
        return data

    async def command_async(self, cmd, args=None, response_len=0):
        if args is None:
            args = ()
        if len(args) > len(self._tx) - 1:
            raise ValueError("too many SI4732 command arguments")
        async with self._command_lock:
            await self._wait_cts_unlocked()
            self._tx[0] = cmd & 0xFF
            for index, value in enumerate(args):
                self._tx[index + 1] = value & 0xFF
            await self._i2c_write_with_retry_async(memoryview(self._tx)[:len(args) + 1])
            if response_len:
                return await self._read_response_unlocked(response_len)
        return None

    async def read_response_async(self, length):
        async with self._command_lock:
            return await self._read_response_unlocked(length)

    async def power_up_async(self, func=0x00, analog_audio=True, xoscen=True, gpo2_output=False):
        arg1 = (0x40 if gpo2_output else 0) | (0x10 if xoscen else 0) | (func & 0x0F)
        opmode = self._OPMODE_ANALOG_AUDIO if analog_audio else self._OPMODE_DIGITAL_AUDIO
        await self.command_async(self._POWER_UP, (arg1, opmode))
        await asyncio.sleep_ms(500 if xoscen else 110)
        await self.wait_cts_async()

    async def power_down_async(self):
        await self.command_async(self._POWER_DOWN)
        await asyncio.sleep_ms(3)

    async def get_revision_async(self):
        resp = await self.command_async(self._GET_REV, (), 9)
        return {"status": resp[0], "part_number": resp[1], "firmware_major": resp[2], "firmware_minor": resp[3], "patch_high": resp[4], "patch_low": resp[5], "component_major": resp[6], "component_minor": resp[7], "chip_revision": resp[8]}

    async def get_int_status_async(self):
        return (await self.command_async(self._GET_INT_STATUS, (), 1))[0]

    async def set_property_async(self, prop, value):
        await self.command_async(self._SET_PROPERTY, (0x00, (prop >> 8) & 0xFF, prop & 0xFF, (value >> 8) & 0xFF, value & 0xFF))
        await asyncio.sleep_ms(1)

    async def get_property_async(self, prop):
        resp = await self.command_async(self._GET_PROPERTY, (0x00, (prop >> 8) & 0xFF, prop & 0xFF), 4)
        return (resp[2] << 8) | resp[3]

    async def fm_tune_freq_async(self, freq_khz, antenna_cap=0, freeze=False, fast=True):
        freq = int(freq_khz // 10)
        await self.command_async(self._FM_TUNE_FREQ, (self._tune_arg(freeze, fast), (freq >> 8) & 0xFF, freq & 0xFF, antenna_cap & 0xFF))

    async def am_tune_freq_async(self, freq_khz, antenna_cap=1, freeze=False, fast=True):
        freq = int(freq_khz)
        await self.command_async(self._AM_TUNE_FREQ, (self._tune_arg(freeze, fast), (freq >> 8) & 0xFF, freq & 0xFF, (antenna_cap >> 8) & 0xFF, antenna_cap & 0xFF))

    async def get_tune_status_async(self, am=False, intack=False, cancel=False):
        arg = (0x01 if intack else 0) | (0x02 if cancel else 0)
        resp = await self.command_async(self._AM_TUNE_STATUS if am else self._FM_TUNE_STATUS, (arg,), 8)
        return {"status": resp[0], "valid": bool(resp[2] & 1), "afc_rail": bool(resp[2] & 2), "frequency": (resp[3] << 8) | resp[4], "rssi": resp[5], "snr": resp[6], "freq_offset": resp[7]}

    async def self_test_async(self):
        if hasattr(self._i2c, "scan") and self._address not in self._i2c.scan():
            raise RuntimeError("SI4732 address 0x%02X not found on I2C bus" % self._address)
        await self.reset_async()
        await self.power_up_async(self.FUNC_FM)
        revision = await self.get_revision_async()
        await self.power_down_async()
        return revision

    async def deinit_async(self):
        try:
            await self.power_down_async()
        except Exception:
            pass
        self._i2c = None
        self._reset_pin = None
        self._log("deinitialized")

    async def aclose(self):
        await self.deinit_async()
