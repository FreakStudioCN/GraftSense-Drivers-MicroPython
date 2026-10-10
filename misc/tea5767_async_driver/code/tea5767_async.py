"""Conservative async adapters for bounded synchronous bus calls."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from tea5767 import Radio

class RadioAsync:
    """Tea5767 transaction facade with a cooperative post-write settle time."""

    def __init__(self, i2c, addr=0x60, freq=0.0, band="US", stereo=True,
                 soft_mute=True, noise_cancel=True, high_cut=True):
        if i2c is None:
            raise ValueError("I2C object cannot be None")
        self._i2c, self._address = i2c, addr
        self.frequency, self.band_limits = freq, band
        self.standby_mode = self.mute_mode = self.search_mode = False
        self.search_direction, self.search_adc_level = 1, 7
        self.stereo_mode, self.soft_mute_mode = stereo, soft_mute
        self.stereo_noise_cancelling_mode, self.high_cut_mode = noise_cancel, high_cut
        self.is_ready = self.is_stereo = False
        self.signal_adc_level = 0

    async def set_frequency_async(self, freq):
        if freq is None: raise ValueError("Frequency value cannot be None")
        self.frequency = freq
        return await self.update_async()
    async def change_freqency_async(self, change):
        if change is None: raise ValueError("Frequency change value cannot be None")
        self.frequency += change; self.search_direction = 1 if change >= 0 else 0
        return await self.update_async()
    async def search_async(self, mode, dir=1, adc=7):
        self.search_mode, self.search_direction = mode, dir
        self.search_adc_level = adc if adc in Radio.ADC else 7
        return await self.update_async()
    async def mute_async(self, mode): self.mute_mode = mode; return await self.update_async()
    async def standby_async(self, mode): self.standby_mode = mode; return await self.update_async()
    async def read_async(self): return Radio.read(self)
    async def update_async(self):
        if self.band_limits == "JP":
            self.frequency = min(max(self.frequency, Radio.FREQ_RANGE_JP[0]), Radio.FREQ_RANGE_JP[1])
        else:
            self.band_limits = "US"; self.frequency = min(max(self.frequency, Radio.FREQ_RANGE_US[0]), Radio.FREQ_RANGE_US[1])
        freq_b = int(4 * (self.frequency * 1000000 + 225000) / 32768)
        buffer = bytearray(5)
        buffer[0] = (freq_b >> 8) | self.mute_mode << 7 | self.search_mode << 6
        buffer[1] = freq_b & 0xFF
        buffer[2] = self.search_direction << 7 | 1 << 4 | self.stereo_mode << 3
        try: buffer[2] += Radio.ADC_BIT[Radio.ADC.index(self.search_adc_level)] << 5
        except ValueError: pass
        buffer[3] = self.standby_mode << 6 | (self.band_limits == "JP") << 5 | 1 << 4
        buffer[3] += self.soft_mute_mode << 3 | self.high_cut_mode << 2 | self.stereo_noise_cancelling_mode << 1
        self._i2c.writeto(self._address, buffer)
        await asyncio.sleep_ms(1)
        return await self.read_async()
    async def aclose(self):
        if not self.standby_mode: await self.standby_async(True)
