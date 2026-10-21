"""Cooperative single-shot adapters for ADS1015/ADS1115 conversions."""

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

import _gs_ads1015_ads1015 as _source

REGISTER_CONVERT = 0x00
REGISTER_CONFIG = 0x01
OS_SINGLE = 0x8000
OS_NOTBUSY = 0x8000
MODE_SINGLE = 0x0100
DR_1600SPS = 0x0080
CMODE_TRAD = 0x0000
CPOL_ACTVLOW = 0x0000
CLAT_NONLAT = 0x0000
CQUE_NONE = 0x0003
GAINS = (0x0000, 0x0200, 0x0400, 0x0600, 0x0800, 0x0A00)
CHANNELS = (0x4000, 0x5000, 0x6000, 0x7000)
DIFFS = {(0, 1): 0x0000, (0, 3): 0x1000, (1, 3): 0x2000, (2, 3): 0x3000}


class _ADSBaseAsync:
    def __init__(self, driver):
        self._driver = driver
        self._lock = asyncio.Lock()
        self._closed = False

    async def _convert_async(self, config):
        async with self._lock:
            self._driver._write_register(REGISTER_CONFIG, config)
            for _ in range(10):
                if self._driver._read_register(REGISTER_CONFIG) & OS_NOTBUSY:
                    return self._driver._read_register(REGISTER_CONVERT)
                await asyncio.sleep_ms(1)
        raise TimeoutError("ADS1115 conversion timeout")

    async def get_gain_async(self):
        return self._driver.gain

    async def set_gain_async(self, gain):
        if not isinstance(gain, int) or not 0 <= gain < len(GAINS):
            raise ValueError("Invalid gain")
        async with self._lock:
            self._driver.gain = gain

    async def aclose(self):
        self._closed = True


class ADS1115Async(_ADSBaseAsync):
    def __init__(self, i2c, address=0x48):
        super().__init__(_source.ADS1115(i2c, address))

    async def read_async(self, channel):
        if channel is None:
            raise ValueError("Channel cannot be None")
        if not isinstance(channel, int):
            raise TypeError("Channel must be int")
        if not 0 <= channel <= 3:
            raise ValueError("Channel number must be 0-3")
        config = (CQUE_NONE | CLAT_NONLAT | CPOL_ACTVLOW | CMODE_TRAD |
                  DR_1600SPS | MODE_SINGLE | OS_SINGLE |
                  GAINS[self._driver.gain] | CHANNELS[channel])
        return await self._convert_async(config)

    async def diff_async(self, channel1, channel2):
        if channel1 is None or channel2 is None:
            raise ValueError("channel1 and channel2 cannot be None")
        if not isinstance(channel1, int) or not isinstance(channel2, int):
            raise TypeError("channels must be int")
        if not 0 <= channel1 <= 3 or not 0 <= channel2 <= 3:
            raise ValueError("channels must be 0-3")
        key = (channel1, channel2)
        if key not in DIFFS:
            raise ValueError("Unsupported differential channel combination: {}".format(key))
        config = (CQUE_NONE | CLAT_NONLAT | CPOL_ACTVLOW | CMODE_TRAD |
                  DR_1600SPS | MODE_SINGLE | OS_SINGLE |
                  GAINS[self._driver.gain] | DIFFS[key])
        return await self._convert_async(config)

    async def alert_start_async(self, channel, threshold):
        async with self._lock:
            return self._driver.alert_start(channel, threshold)

    async def alert_read_async(self):
        async with self._lock:
            return self._driver.alert_read()


class ADS1015Async(ADS1115Async):
    def __init__(self, i2c, address=0x48):
        _ADSBaseAsync.__init__(self, _source.ADS1015(i2c, address))

    async def read_async(self, channel):
        return (await super().read_async(channel)) >> 4

    async def diff_async(self, channel1, channel2):
        return (await super().diff_async(channel1, channel2)) >> 4

    async def alert_start_async(self, channel, threshold):
        if threshold is None:
            raise ValueError("Threshold cannot be None")
        if not isinstance(threshold, int):
            raise TypeError("Threshold must be int")
        if not -2048 <= threshold <= 2047:
            raise ValueError("Threshold must be between -2048 and 2047 for ADS1015")
        async with self._lock:
            return self._driver.alert_start(channel, threshold)

    async def alert_read_async(self):
        return (await super().alert_read_async()) >> 4

