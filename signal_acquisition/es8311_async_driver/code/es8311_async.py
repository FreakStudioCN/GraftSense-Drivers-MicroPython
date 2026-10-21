"""Cooperative ES8311 register adapter."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import es8311 as _source

ES8311ClockConfigAsync = _source.ES8311ClockConfig


class ES8311Async:
    def __init__(self, i2c, address=_source.ES8311.I2C_DEFAULT_ADDR, debug=False):
        self._driver = _source.ES8311(i2c, address, debug)
        self._lock = asyncio.Lock()
        self._closed = False

    async def init_async(self, clk_cfg, res_in, res_out):
        async with self._lock:
            self._driver._write_reg(_source.ES8311_RESET_REG00, 0x1F)
            await asyncio.sleep_ms(20)
            self._driver._write_reg(_source.ES8311_RESET_REG00, 0x00)
            self._driver._write_reg(_source.ES8311_RESET_REG00, 0x80)
            self._driver.clock_config(clk_cfg, res_out)
            self._driver.fmt_config(res_in, res_out)
            self._driver._write_reg(_source.ES8311_SYSTEM_REG0D, 0x01)
            self._driver._write_reg(_source.ES8311_SYSTEM_REG0E, 0x02)
            self._driver._write_reg(_source.ES8311_SYSTEM_REG12, 0x00)
            self._driver._write_reg(_source.ES8311_SYSTEM_REG13, 0x10)
            self._driver._write_reg(_source.ES8311_ADC_REG1C, 0x6A)
            self._driver._write_reg(_source.ES8311_DAC_REG37, 0x08)

    async def clock_config_async(self, clk_cfg, res):
        async with self._lock:
            return self._driver.clock_config(clk_cfg, res)

    async def fmt_config_async(self, res_in, res_out):
        async with self._lock:
            return self._driver.fmt_config(res_in, res_out)

    async def sample_frequency_config_async(self, mclk_frequency, sample_frequency):
        async with self._lock:
            return self._driver.sample_frequency_config(mclk_frequency, sample_frequency)

    async def voice_volume_set_async(self, volume):
        async with self._lock:
            return self._driver.voice_volume_set(volume)

    async def voice_volume_get_async(self):
        return self._driver.voice_volume_get()

    async def microphone_config_async(self, digital_mic):
        async with self._lock:
            return self._driver.microphone_config(digital_mic)

    async def resolution_config_async(self, res, reg):
        return self._driver.resolution_config(res, reg)

    async def deinit_async(self):
        async with self._lock:
            return self._driver.deinit()

    async def aclose(self):
        if self._closed:
            return
        try:
            await self.deinit_async()
        finally:
            self._closed = True

