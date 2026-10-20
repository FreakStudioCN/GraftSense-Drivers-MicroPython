"""Cooperative ADS1115 adapter with a single I2C transaction lock."""

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

import _gs_ads1115_ads1115 as _source
from machine import Pin
import time


class ADS1115Async:
    def __init__(self, i2c, address=0x48, gain=2, alert_pin=None, callback=None):
        # Do not pass an arbitrary callback into the source IRQ/schedule chain.
        self._driver = _source.ADS1115(i2c, address, gain)
        self._lock = asyncio.Lock()
        self._closed = False
        self._alert_pending = False
        self._alert_pin = None
        self._alert_callback = callback
        if alert_pin is not None:
            self._alert_pin = alert_pin if hasattr(alert_pin, "irq") else Pin(alert_pin, Pin.IN)
            self._alert_pin.irq(handler=self._alert_irq, trigger=Pin.IRQ_FALLING)

    def _alert_irq(self, _pin):
        """IRQ boundary: only write an already allocated flag."""
        self._alert_pending = True

    async def wait_alert_async(self, timeout_ms=1000):
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while not self._alert_pending:
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                raise TimeoutError("ADS1115 alert timeout")
            await asyncio.sleep_ms(1)
        self._alert_pending = False
        if self._alert_callback is not None:
            result = self._alert_callback(self._alert_pin)
            if hasattr(result, "send") or hasattr(result, "__await__"):
                await result

    async def raw_to_v_async(self, raw):
        return self._driver.raw_to_v(raw)

    async def set_conv_async(self, rate=4, channel1=0, channel2=None):
        async with self._lock:
            return self._driver.set_conv(rate, channel1, channel2)

    async def read_async(self, rate=4, channel1=0, channel2=None, timeout_ms=1000):
        if rate not in range(len(_source.ADS1115.RATES)):
            raise ValueError("Invalid rate: {}".format(rate))
        if channel1 not in range(4) or (channel2 is not None and channel2 not in range(4)):
            raise ValueError("Invalid channel: {}".format(channel1))
        async with self._lock:
            config = (_source.ADS1115.CQUE_NONE | _source.ADS1115.CLAT_NONLAT |
                      _source.ADS1115.CPOL_ACTVLOW | _source.ADS1115.CMODE_TRAD |
                      _source.ADS1115.RATES[rate] | _source.ADS1115.MODE_SINGLE |
                      _source.ADS1115.OS_SINGLE | _source.ADS1115.GAINS[self._driver.gain_index] |
                      _source.ADS1115.CHANNELS.get((channel1, channel2), _source.ADS1115.MUX_SINGLE_0))
            self._driver._write_register(_source.ADS1115.REGISTER_CONFIG, config)
            for _ in range(timeout_ms):
                if self._driver._read_register(_source.ADS1115.REGISTER_CONFIG) & _source.ADS1115.OS_NOTBUSY:
                    result = self._driver._read_register(_source.ADS1115.REGISTER_CONVERT)
                    return result if result < 32768 else result - 65536
                await asyncio.sleep_ms(1)
        raise TimeoutError("ADS1115 conversion timeout")

    async def read_rev_async(self):
        async with self._lock:
            return self._driver.read_rev()

    async def alert_start_async(self, rate=4, channel1=0, channel2=None, threshold_high=0x4000, threshold_low=0, latched=False):
        async with self._lock:
            return self._driver.alert_start(rate, channel1, channel2, threshold_high, threshold_low, latched)

    async def conversion_start_async(self, rate=4, channel1=0, channel2=None):
        async with self._lock:
            return self._driver.conversion_start(rate, channel1, channel2)

    async def alert_read_async(self):
        async with self._lock:
            return self._driver.alert_read()

    async def aclose(self):
        if self._closed:
            return
        self._closed = True
        if self._alert_pin is not None:
            self._alert_pin.irq(handler=None)

