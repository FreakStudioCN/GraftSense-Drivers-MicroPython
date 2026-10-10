try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from tca9554 import TCA9554 as _TCA9554, TCA9554_DEFAULT_ADDR

class TCA9554(_TCA9554):
    def __init__(self, i2c, address=TCA9554_DEFAULT_ADDR, config=0xFF, output=0x00, debug=False):
        self._pending_init, self._initialized = (i2c, address, config, output, debug), False
    async def initialize_async(self):
        if not self._initialized:
            _TCA9554.__init__(self, *self._pending_init)
            self._initialized = True
    def _ready(self):
        if not self._initialized: raise RuntimeError("call initialize_async() before use")
    async def is_connected_async(self): self._ready(); return self.is_connected()
    async def pin_mode_async(self, pin, mode): self._ready(); self.pin_mode(pin, mode)
    async def pin_mode8_async(self, mask): self._ready(); self.pin_mode8(mask)
    async def write_async(self, pin, value): self._ready(); self.write(pin, value)
    async def write_port_async(self, value): self._ready(); self.write_port(value)
    async def read_async(self, pin): self._ready(); return self.read(pin)
    async def read_input8_async(self): self._ready(); return self.read_input8()
    async def read_output8_async(self): self._ready(); return self.read_output8()
    async def set_polarity_async(self, pin, invert): self._ready(); self.set_polarity(pin, invert)
    async def set_polarity8_async(self, mask): self._ready(); self.set_polarity8(mask)
    async def deinit_async(self):
        if self._initialized: self.deinit(); self._initialized = False
    async def aclose(self): await self.deinit_async()

TCA9554Async = TCA9554
