"""Conservative async adapters for bounded synchronous bus calls."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time

from silicon5351 import *

class _SI5351State(SI5351_I2C):
    """Preserve source methods without running synchronous initialization."""
    def __init__(self):
        pass


class SI5351_I2CAsync:
    """Async facade; each delegated call remains a short sync transaction."""

    def __init__(self, i2c, crystal, load=3, address=0x60):
        self._driver = _SI5351State()
        self._driver.i2c, self._driver.crystal, self._driver.address = i2c, crystal, address
        self._driver.vco, self._driver.pll, self._driver.quadrature = {}, {}, {}
        self._driver.invert, self._driver.drive_strength, self._driver.div = {}, {}, {}
        self._load, self._lock, self._initialized = load, asyncio.Lock(), False

    async def initialize_async(self, timeout_ms=1000):
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        async with self._lock:
            while self._driver._read(self._driver.SI5351_REGISTER_DEVICE_STATUS) & 0x80:
                if time.ticks_diff(deadline, time.ticks_ms()) <= 0: raise OSError("SI5351 initialization timeout")
                await asyncio.sleep_ms(1)
            self._driver._write(self._driver.SI5351_REGISTER_OUTPUT_ENABLE_CONTROL, 0xff)
            self._driver._write_bulk(self._driver.SI5351_REGISTER_CLK0_CONTROL, [self._driver.SI5351_CLK_POWERDOWN] * 8)
            self._driver._write(self._driver.SI5351_REGISTER_CRYSTAL_LOAD, self._load << 6)
            self._initialized = True

    async def write_config_async(self, reg, whole, num, denom, rdiv):
        async with self._lock:
            return self._driver.write_config(reg, whole, num, denom, rdiv)

    async def set_phase_async(self, output, div):
        async with self._lock:
            return self._driver.set_phase(output, div)

    async def reset_pll_async(self, pll):
        async with self._lock:
            return self._driver.reset_pll(pll)

    async def init_multisynth_async(self, output, integer_mode):
        async with self._lock:
            return self._driver.init_multisynth(output, integer_mode)

    async def approximate_fraction_async(self, n, d, max_denom):
        async with self._lock:
            return self._driver.approximate_fraction(n, d, max_denom)

    async def init_clock_async(self, output, pll, quadrature=False, invert=False, drive_strength=3):
        async with self._lock:
            return self._driver.init_clock(output, pll, quadrature, invert, drive_strength)

    async def enable_output_async(self, output):
        async with self._lock:
            return self._driver.enable_output(output)

    async def disable_output_async(self, output):
        async with self._lock:
            return self._driver.disable_output(output)

    async def setup_pll_async(self, pll, mul, num=0, denom=1):
        async with self._lock:
            return self._driver.setup_pll(pll, mul, num, denom)

    async def setup_multisynth_async(self, output, div, num=0, denom=1, rdiv=0):
        async with self._lock:
            return self._driver.setup_multisynth(output, div, num, denom, rdiv)

    async def set_freq_fixedpll_async(self, output, freq):
        async with self._lock:
            return self._driver.set_freq_fixedpll(output, freq)

    async def set_freq_fixedms_async(self, output, freq):
        async with self._lock:
            return self._driver.set_freq_fixedms(output, freq)

    async def disabled_states_async(self, output, state):
        async with self._lock:
            return self._driver.disabled_states(output, state)

    async def disable_oeb_async(self, mask):
        async with self._lock:
            return self._driver.disable_oeb(mask)

    async def aclose(self):
        return None

