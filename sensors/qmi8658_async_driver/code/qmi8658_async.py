"""QMI8658 async facade with cooperative hardware-reset initialization."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from qmi8658 import QMI8658

ADDR = 0x6B


class QMI8658Async(QMI8658):
    def __init__(self, i2c, address=ADDR, reset_pin=None, verify=True, debug=False):
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance with readfrom_mem()")
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))
        if not isinstance(verify, bool) or not isinstance(debug, bool):
            raise ValueError("verify and debug must be bool")
        self._i2c = i2c
        self._addr = address
        self._reset_pin = reset_pin
        self._debug = debug
        self._verify = verify
        self._initialized = False

    async def initialize_async(self):
        if self._initialized:
            return
        if self._reset_pin is not None:
            await self.reset_async()
        if self._verify:
            chip_id = self.who_am_i()
            if chip_id != self.WHO_AM_I_VALUE:
                raise RuntimeError("QMI8658 WHO_AM_I mismatch: expected 0x%02X, got 0x%02X" % (self.WHO_AM_I_VALUE, chip_id))
        self._log("Init complete, applying default config")
        self.configure_default()
        self._initialized = True

    async def who_am_i_async(self):
        return self.who_am_i()

    async def revision_async(self):
        return self.revision()

    async def reset_async(self):
        if self._reset_pin is None:
            raise RuntimeError("reset_pin is required for hardware reset")
        self._log("Hardware reset")
        self._reset_pin.value(0)
        await asyncio.sleep_ms(10)
        self._reset_pin.value(1)
        await asyncio.sleep_ms(50)

    async def configure_default_async(self):
        self.configure_default()

    async def read_raw_async(self):
        return self.read_raw()

    async def read_xyz_async(self):
        return self.read_xyz()

    async def deinit_async(self):
        self.deinit()
        self._initialized = False

    async def aclose(self):
        await self.deinit_async()