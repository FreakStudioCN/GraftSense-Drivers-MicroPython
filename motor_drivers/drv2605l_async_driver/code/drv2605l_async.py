"""Conservative async adapters for bounded synchronous bus calls."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from drv2605l import DRV2605, Effect, Pause
from micropython import const

_DRV2605_REG_GO = const(12)
_GO_BIT = const(1)
_DEFAULT_GO_TIMEOUT_MS = const(5000)
_GO_POLL_INTERVAL_MS = const(10)

class EffectAsync(Effect):
    async def get_raw_value_async(self): return self.raw_value
    async def get_id_async(self): return self.id
    async def set_id_async(self, effect_id): self.id = effect_id

class PauseAsync(Pause):
    async def get_raw_value_async(self): return self.raw_value
    async def get_duration_async(self): return self.duration
    async def set_duration_async(self, duration): self.duration = duration

class DRV2605Async:
    """Async-only facade retaining the source register and GO-bit protocol."""

    def __init__(self, i2c, address=0x5A):
        self._driver = DRV2605(i2c, address=address)

    async def play_async(self):
        return self._driver.play()

    async def play_effect_async(self, timeout_ms=None):
        self._driver._write_u8(_DRV2605_REG_GO, 1)
        if timeout_ms == 0: return True
        if timeout_ms is None: timeout_ms = _DEFAULT_GO_TIMEOUT_MS
        for _ in range((timeout_ms + _GO_POLL_INTERVAL_MS - 1) // _GO_POLL_INTERVAL_MS):
            if not (self._driver._read_u8(_DRV2605_REG_GO) & _GO_BIT): return True
            await asyncio.sleep_ms(_GO_POLL_INTERVAL_MS)
        return False

    async def stop_async(self): return self._driver.stop()
    async def get_mode_async(self): return self._driver.mode
    async def set_mode_async(self, value): self._driver.mode = value
    async def get_library_async(self): return self._driver.library
    async def set_library_async(self, value): self._driver.library = value
    async def get_realtime_value_async(self): return self._driver.realtime_value
    async def set_realtime_value_async(self, value): self._driver.realtime_value = value
    async def get_sequence_async(self):
        return tuple(effect.id for effect in self._driver.sequence)
    async def set_waveform_async(self, effect_id, slot=0): return self._driver.set_waveform(effect_id, slot)
    async def use_ERM_async(self): return self._driver.use_ERM()
    async def use_LRM_async(self): return self._driver.use_LRM()
    async def deinit(self): return self._driver.deinit()
    async def aclose(self): return await self.deinit()
