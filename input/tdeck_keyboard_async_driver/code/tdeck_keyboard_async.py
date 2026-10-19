"""Async lifecycle and polling adapter for the T-Deck keyboard."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from _gs_tdeck_keyboard_tdeck_keyboard import TDeckKeyboard, TDECK_KEYBOARD_ADDR


class TDeckKeyboardAsync(TDeckKeyboard):
    def __init__(self, i2c, address=TDECK_KEYBOARD_ADDR, power_pin=None, startup_ms=0, debug=False):
        if startup_ms < 0: raise ValueError("startup_ms must be >= 0")
        self._pending_init, self._initialized = (i2c, address, power_pin, startup_ms, debug), False
    async def initialize_async(self):
        if not self._initialized:
            i2c, address, power_pin, startup_ms, debug = self._pending_init
            TDeckKeyboard.__init__(self, i2c, address, power_pin, 0, debug)
            self._initialized = True
            if startup_ms: await asyncio.sleep_ms(startup_ms)
    def _ready(self):
        if not self._initialized: raise RuntimeError("call initialize_async() before use")
    async def is_present_async(self): self._ready(); return self.is_present()
    async def set_brightness_async(self, duty): self._ready(); self.set_brightness(duty)
    async def set_default_brightness_async(self, duty): self._ready(); self.set_default_brightness(duty)
    async def set_raw_mode_async(self): self._ready(); self.set_raw_mode()
    async def set_key_mode_async(self): self._ready(); self.set_key_mode()
    async def read_keycode_async(self): self._ready(); return self.read_keycode()
    async def read_key_async(self): self._ready(); return self.read_key()
    async def read_key_name_async(self): self._ready(); return self.read_key_name()
    async def read_raw_async(self): self._ready(); return self.read_raw()
    async def pressed_positions_async(self, raw=None): self._ready(); return self.pressed_positions(raw)
    async def pressed_keys_async(self, raw=None, include_special=False): self._ready(); return self.pressed_keys(raw, include_special)
    async def decode_keycode_async(self, code): return self.decode_keycode(code)
    async def self_test_async(self, verbose=True): self._ready(); return self.self_test(verbose)
    async def wait_key_async(self, timeout_ms=1000, poll_ms=10):
        self._ready()
        if timeout_ms < 0 or poll_ms < 0: raise ValueError("timeout_ms and poll_ms must be >= 0")
        attempts = timeout_ms // max(1, poll_ms) + 1
        for _ in range(attempts):
            key = self.read_key()
            if key is not None: return key
            if poll_ms == 0: return None
            await asyncio.sleep_ms(poll_ms)
        return None
    async def deinit_async(self, power_off=False):
        if self._initialized:
            self.deinit(power_off)
            self._initialized = False
    async def aclose(self): await self.deinit_async()
