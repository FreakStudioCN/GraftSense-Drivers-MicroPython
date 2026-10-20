"""MPL3115A2 adapter with cooperative data-ready initialization."""

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

import time
from mpl3115a2 import MPL3115A2, MPL3115A2exception

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class MPL3115A2Async(MPL3115A2):
    """Defer the source status wait from construction to start_async()."""

    def __init__(self, i2c, mode=MPL3115A2.PRESSURE):
        self._defer_status_wait = True
        super().__init__(i2c, mode)
        self._defer_status_wait = False
        self._ready = False

    def _read_status(self):
        if getattr(self, '_defer_status_wait', False):
            return True
        return super()._read_status()

    async def start_async(self, timeout_ms=1000):
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while True:
            self.i2c.readfrom_mem_into(MPL3115A2.MPL3115_I2CADDR, MPL3115A2.MPL3115_STATUS, self.STA_reg)
            if self.STA_reg[0] & 0x04:
                self._ready = True
                return
            if self.STA_reg[0] != 0:
                raise MPL3115A2exception('Error with MPL3115A2')
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                raise TimeoutError('MPL3115A2 data-ready timeout')
            await asyncio.sleep_ms(10)

    async def pressure_async(self):
        return self.pressure()

    async def altitude_async(self):
        return self.altitude()

    async def temperature_async(self):
        return self.temperature()

    async def aclose(self):
        return None

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================