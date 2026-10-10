"""Cooperative single-shot adapters for ADS1015/ADS1115 conversions."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import ads1015 as _source


class _ADSBaseAsync:
    def __init__(self, driver):
        self._driver = driver
        self._lock = asyncio.Lock()
        self._closed = False

    async def _convert_async(self, config):
        async with self._lock:
            self._driver._write_register(_source._REGISTER_CONFIG, config)
            for _ in range(10):
                if self._driver._read_register(_source._REGISTER_CONFIG) & _source._OS_NOTBUSY:
                    return self._driver._read_register(_source._REGISTER_CONVERT)
                await asyncio.sleep_ms(1)
        raise TimeoutError("ADS1115 conversion timeout")

    async def get_gain_async(self):
        return self._driver.gain

    async def set_gain_async(self, gain):
        if gain not in _source._GAINS:
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
        config = (_source._CQUE_NONE | _source._CLAT_NONLAT |
                  _source._CPOL_ACTVLOW | _source._CMODE_TRAD |
                  _source._DR_1600SPS | _source._MODE_SINGLE |
                  _source._OS_SINGLE | _source._GAINS[self._driver.gain] |
                  _source._CHANNELS[channel])
        return await self._convert_async(config)

    async def diff_async(self, channel1, channel2):
        if channel1 is None or channel2 is None:
            raise ValueError("channel1 and channel2 cannot be None")
        if not isinstance(channel1, int) or not isinstance(channel2, int):
            raise TypeError("channels must be int")
        if not 0 <= channel1 <= 3 or not 0 <= channel2 <= 3:
            raise ValueError("channels must be 0-3")
        key = (channel1, channel2)
        if key not in _source._DIFFS:
            raise ValueError("Unsupported differential channel combination: {}".format(key))
        config = (_source._CQUE_NONE | _source._CLAT_NONLAT |
                  _source._CPOL_ACTVLOW | _source._CMODE_TRAD |
                  _source._DR_1600SPS | _source._MODE_SINGLE |
                  _source._OS_SINGLE | _source._GAINS[self._driver.gain] |
                  _source._DIFFS[key])
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

