"""Cooperative ES7210 register configuration facade."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import es7210 as _source


class ES7210Async:
    """Expose only explicit async operations while retaining source register order."""

    def __init__(self, i2c, address=_source.DEFAULT_ADDRESS, sample_rate=16000,
                 bits_per_sample=_source.BITS_16, mic_gain_db=24, tdm=False,
                 init=True, debug=False):
        # Source construction keeps its validation/state but must not run its
        # synchronous configure path.
        self._driver = _source.ES7210(
            i2c, address, sample_rate, bits_per_sample, mic_gain_db, tdm,
            init=False, debug=debug)
        self._lock = asyncio.Lock()
        self._closed = False
        # Construction cannot safely perform the source's register I/O.  Keep
        # this flag observable and provide create_async() for source-equivalent
        # initialization before the object is handed to application code.
        self._initialize = bool(init)

    @classmethod
    async def create_async(cls, i2c, address=_source.DEFAULT_ADDRESS,
                           sample_rate=16000, bits_per_sample=_source.BITS_16,
                           mic_gain_db=24, tdm=False, init=True, debug=False):
        device = cls(i2c, address, sample_rate, bits_per_sample, mic_gain_db,
                     tdm, init=init, debug=debug)
        if init:
            await device.configure_async()
        return device

    async def _read_locked(self, reg):
        buffer = bytearray(1)
        for attempt in range(_source.I2C_RETRIES + 1):
            try:
                self._driver._i2c.readfrom_mem_into(self._driver._addr, reg & 0xFF, buffer)
                return buffer[0]
            except OSError as error:
                if attempt == _source.I2C_RETRIES:
                    raise RuntimeError(
                        "ES7210 I2C read failed addr=0x%02X reg=0x%02X after %d retries"
                        % (self._driver._addr, reg & 0xFF, _source.I2C_RETRIES)) from error
                await asyncio.sleep_ms(_source.I2C_RETRY_DELAY_MS)

    async def _write_locked(self, reg, value):
        buffer = bytearray((value & 0xFF,))
        for attempt in range(_source.I2C_RETRIES + 1):
            try:
                self._driver._i2c.writeto_mem(self._driver._addr, reg & 0xFF, buffer)
                return
            except OSError as error:
                if attempt == _source.I2C_RETRIES:
                    raise RuntimeError(
                        "ES7210 I2C write failed addr=0x%02X reg=0x%02X value=0x%02X after %d retries"
                        % (self._driver._addr, reg & 0xFF, value & 0xFF, _source.I2C_RETRIES)) from error
                await asyncio.sleep_ms(_source.I2C_RETRY_DELAY_MS)

    async def _update_bits_locked(self, reg, mask, value):
        current = await self._read_locked(reg)
        await self._write_locked(reg, (current & (~mask & 0xFF)) | (value & mask))

    async def scan_async(self):
        async with self._lock:
            if not hasattr(self._driver._i2c, "scan"):
                raise RuntimeError("I2C bus does not support scan()")
            return self._driver._addr in self._driver._i2c.scan()

    async def read_reg_async(self, reg):
        async with self._lock:
            return await self._read_locked(reg)

    async def write_reg_async(self, reg, value):
        async with self._lock:
            await self._write_locked(reg, value)

    async def update_bits_async(self, reg, mask, value):
        async with self._lock:
            await self._update_bits_locked(reg, mask, value)

    async def reset_async(self):
        async with self._lock:
            await self._write_locked(_source.RESET_REG00, 0xFF)
            await asyncio.sleep_ms(2)
            await self._write_locked(_source.RESET_REG00, 0x32)
            await asyncio.sleep_ms(2)

    async def configure_i2s_format_async(self, bits_per_sample=None, tdm=None):
        async with self._lock:
            bits = self._driver.bits_per_sample if bits_per_sample is None else bits_per_sample
            tdm_mode = self._driver.tdm if tdm is None else bool(tdm)
            if bits not in _source.BITS_REG_MAP:
                raise ValueError("bits_per_sample must be 16, 18, 20, 24, or 32, got %s" % repr(bits))
            await self._write_locked(_source.SDP_INTERFACE1_REG11, _source.BITS_REG_MAP[bits])
            await self._write_locked(_source.SDP_INTERFACE2_REG12, 0x02 if tdm_mode else 0x00)
            self._driver.bits_per_sample = bits
            self._driver.tdm = tdm_mode

    async def configure_sample_rate_async(self, sample_rate):
        async with self._lock:
            mclk = sample_rate * 256
            coeff = _source.SAMPLE_RATE_COEFFICIENTS.get((mclk, sample_rate))
            if coeff is None:
                raise ValueError("Unsupported sample_rate/mclk pair: %d Hz (mclk=%d)" % (sample_rate, mclk))
            adc_div, dll, doubler, osr, mclk_src, lrck_h, lrck_l = coeff
            await self._write_locked(_source.MAINCLK_REG02, adc_div | (doubler << 6) | (dll << 7))
            await self._write_locked(_source.OSR_REG07, osr)
            await self._write_locked(_source.MASTER_CLK_REG03, mclk_src)
            await self._write_locked(_source.LRCK_DIVH_REG04, lrck_h)
            await self._write_locked(_source.LRCK_DIVL_REG05, lrck_l)
            self._driver.sample_rate = sample_rate

    async def set_mic_gain_async(self, mic_gain_db):
        async with self._lock:
            reg_value = self._driver._gain_to_reg(mic_gain_db)
            for reg in (_source.MIC1_GAIN_REG43, _source.MIC2_GAIN_REG44,
                        _source.MIC3_GAIN_REG45, _source.MIC4_GAIN_REG46):
                await self._update_bits_locked(reg, 0x10, 0x10)
                await self._update_bits_locked(reg, 0x0F, reg_value)
            self._driver.mic_gain_db = mic_gain_db

    async def mute_async(self, enabled=True):
        async with self._lock:
            await self._write_locked(_source.ADC_AUTOMUTE_REG13, 0x0F if enabled else 0x00)

    async def configure_async(self, sample_rate=None, bits_per_sample=None, mic_gain_db=None, tdm=None):
        # Keep source order: reset, clock/HPF, format, rate, gain, power-up.
        async with self._lock:
            if sample_rate is not None:
                self._driver.sample_rate = sample_rate
            if bits_per_sample is not None:
                self._driver.bits_per_sample = bits_per_sample
            if mic_gain_db is not None:
                self._driver.mic_gain_db = mic_gain_db
            if tdm is not None:
                self._driver.tdm = bool(tdm)
            await self._write_locked(_source.RESET_REG00, 0xFF)
            await asyncio.sleep_ms(2)
            await self._write_locked(_source.RESET_REG00, 0x32)
            await asyncio.sleep_ms(2)
            for reg, value in ((_source.CLOCK_OFF_REG01, 0x3F), (_source.TIME_CONTROL0_REG09, 0x30),
                               (_source.TIME_CONTROL1_REG0A, 0x30), (_source.ADC12_HPF2_REG23, 0x2A),
                               (_source.ADC12_HPF1_REG22, 0x0A), (_source.ADC34_HPF2_REG20, 0x0A),
                               (_source.ADC34_HPF1_REG21, 0x2A)):
                await self._write_locked(reg, value)
            await self._update_bits_locked(_source.MODE_CONFIG_REG08, 0x01, 0x00)
            for reg, value in ((_source.ANALOG_REG40, 0xC3), (_source.MIC12_BIAS_REG41, 0x70),
                               (_source.MIC34_BIAS_REG42, 0x70)):
                await self._write_locked(reg, value)
            bits = self._driver.bits_per_sample
            if bits not in _source.BITS_REG_MAP:
                raise ValueError("bits_per_sample must be 16, 18, 20, 24, or 32, got %s" % repr(bits))
            await self._write_locked(_source.SDP_INTERFACE1_REG11, _source.BITS_REG_MAP[bits])
            await self._write_locked(_source.SDP_INTERFACE2_REG12, 0x02 if self._driver.tdm else 0x00)
            mclk = self._driver.sample_rate * 256
            coeff = _source.SAMPLE_RATE_COEFFICIENTS.get((mclk, self._driver.sample_rate))
            if coeff is None:
                raise ValueError("Unsupported sample_rate/mclk pair: %d Hz (mclk=%d)" % (self._driver.sample_rate, mclk))
            adc_div, dll, doubler, osr, mclk_src, lrck_h, lrck_l = coeff
            for reg, value in ((_source.MAINCLK_REG02, adc_div | (doubler << 6) | (dll << 7)),
                               (_source.OSR_REG07, osr), (_source.MASTER_CLK_REG03, mclk_src),
                               (_source.LRCK_DIVH_REG04, lrck_h), (_source.LRCK_DIVL_REG05, lrck_l)):
                await self._write_locked(reg, value)
            reg_value = self._driver._gain_to_reg(self._driver.mic_gain_db)
            for reg in (_source.MIC1_GAIN_REG43, _source.MIC2_GAIN_REG44,
                        _source.MIC3_GAIN_REG45, _source.MIC4_GAIN_REG46):
                await self._update_bits_locked(reg, 0x10, 0x10)
                await self._update_bits_locked(reg, 0x0F, reg_value)
            for reg, value in ((_source.MIC1_POWER_REG47, 0x08), (_source.MIC2_POWER_REG48, 0x08),
                               (_source.MIC3_POWER_REG49, 0x08), (_source.MIC4_POWER_REG4A, 0x08),
                               (_source.POWER_DOWN_REG06, 0x04), (_source.MIC12_POWER_REG4B, 0x0F),
                               (_source.MIC34_POWER_REG4C, 0x0F), (_source.RESET_REG00, 0x71),
                               (_source.RESET_REG00, 0x41)):
                await self._write_locked(reg, value)

    async def self_test_async(self, timeout_ms=1000):
        async with self._lock:
            if not hasattr(self._driver._i2c, "scan") or self._driver._addr not in self._driver._i2c.scan():
                raise RuntimeError("ES7210 address 0x%02X not found on I2C bus" % self._driver._addr)
            test_reg = _source.TIME_CONTROL0_REG09
            original = await self._read_locked(test_reg)
            try:
                await self._write_locked(test_reg, 0x30)
                attempts = max(1, timeout_ms // 5)
                for _ in range(attempts):
                    if await self._read_locked(test_reg) == 0x30:
                        return True
                    await asyncio.sleep_ms(5)
                raise RuntimeError("ES7210 self-test timed out reading back reg 0x%02X" % test_reg)
            finally:
                await self._write_locked(test_reg, original)

    async def deinit_async(self):
        await self.aclose()

    async def aclose(self):
        if self._closed:
            return
        async with self._lock:
            if self._closed:
                return
            await self._write_locked(_source.ADC_AUTOMUTE_REG13, 0x0F)
            await self._write_locked(_source.POWER_DOWN_REG06, 0xFF)
            self._closed = True

