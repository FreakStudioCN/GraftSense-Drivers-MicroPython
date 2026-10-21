"""Conservative async adapters for bounded synchronous bus calls."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

MCP3421_REFERENCE_VOLTAGE = 2.048


class I2cAdapterAsync:
    """Minimal async-package adapter matching the source construction shape."""

    def __init__(self, i2c):
        self.i2c = i2c


class Mcp3421Async:
    """Composition-based async facade for the MCP3421 direct I2C protocol."""

    def __init__(self, i2c, model="mcp3421", address=0x68):
        if not 0x68 <= address < 0x70:
            raise ValueError("Invalid I2C device address: 0x%x" % address)
        self._i2c, self._address, self._model = i2c, address, model
        self._lock = asyncio.Lock()
        self._raw_data_rate = self._raw_gain = self._single_shot = None
        self._resolution = self._data_ready = None
        self._closed = False

    @staticmethod
    def _resolution_for_rate(data_rate_raw):
        if data_rate_raw not in range(4):
            raise ValueError("Invalid data_rate_raw: %s" % data_rate_raw)
        return 12 + 2 * data_rate_raw

    @staticmethod
    def _gain_for_raw(gain_raw):
        if gain_raw not in range(4):
            raise ValueError("Invalid gain_raw: %s" % gain_raw)
        return 2 ** gain_raw

    async def _read_frame_locked(self):
        # Source always reads its four-byte buffer; config is the final byte.
        frame = bytearray(4)
        self._i2c.readfrom_into(self._address, frame)
        config = frame[-1]
        self._data_ready = not bool(config & 0x80)
        self._raw_data_rate = (config >> 2) & 0x03
        self._raw_gain = config & 0x03
        self._single_shot = not bool(config & 0x10)
        self._resolution = self._resolution_for_rate(self._raw_data_rate)
        return frame

    async def get_raw_config_async(self):
        async with self._lock:
            return (await self._read_frame_locked())[-1]

    async def start_measurement_async(self, single_shot, data_rate_raw, gain_raw,
                                      channel=0, differential_channel=True):
        if channel != 0 or not differential_channel:
            raise ValueError("MCP3421 supports only differential channel 0")
        resolution = self._resolution_for_rate(data_rate_raw)
        self._gain_for_raw(gain_raw)
        config = ((0x80 if single_shot else 0x00) | (0x00 if single_shot else 0x10) |
                  ((data_rate_raw & 0x03) << 2) | (gain_raw & 0x03))
        async with self._lock:
            self._i2c.writeto(self._address, bytes((config,)))
            self._single_shot, self._raw_data_rate = bool(single_shot), data_rate_raw
            self._raw_gain, self._resolution, self._data_ready = gain_raw, resolution, False

    async def get_conversion_cycle_time_async(self):
        if self._raw_data_rate is None:
            await self.get_raw_config_async()
        return 1 + int(1000000 / (240, 60, 15, 3.75)[self._raw_data_rate])

    async def get_raw_value_async(self):
        async with self._lock:
            frame = await self._read_frame_locked()
            if not self._data_ready:
                return None
            if self._raw_data_rate < 3:
                value = (frame[0] << 8) | frame[1]
                return value - 0x10000 if value & 0x8000 else value
            value = (frame[0] << 16) | (frame[1] << 8) | frame[2]
            return value - 0x1000000 if value & 0x800000 else value

    async def get_value_async(self, raw=True):
        value = await self.get_raw_value_async()
        if raw or value is None:
            return value
        return value * (2 * MCP3421_REFERENCE_VOLTAGE /
                        (self._gain_for_raw(self._raw_gain) * (2 ** self._resolution)))

    async def data_ready_async(self):
        async with self._lock:
            await self._read_frame_locked()
            return self._data_ready if self._single_shot or self._raw_data_rate == 3 else True

    async def aclose(self):
        self._closed = True


class Mcp342XAsync(Mcp3421Async):
    """Source-name-compatible async MCP342X facade for an I2C adapter."""

    def __init__(self, adapter, model="mcp3421", address=0x68):
        super().__init__(adapter.i2c, model, address)

